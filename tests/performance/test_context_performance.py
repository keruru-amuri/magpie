"""
Performance tests for the context management system.
"""
import pytest
import time
import uuid
import random
import string
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session

from app.models.conversation import Conversation, Message, MessageRole, AgentType
from app.models.context import (
    ContextWindow, ContextItem, ContextType, ContextPriority
)
from app.repositories.conversation import ConversationRepository
from app.repositories.context import (
    ContextWindowRepository, ContextItemRepository
)
from app.services.context_service import ContextService
from app.core.context.pruning import (
    PriorityBasedPruning, RelevanceBasedPruning, TimeBasedPruning,
    HybridPruningStrategy
)


class TestContextPerformance:
    """
    Performance tests for the context management system.
    """
    
    @pytest.fixture
    def db_session(self):
        """
        Create a database session.
        """
        from app.core.db.connection import DatabaseConnectionFactory
        session = DatabaseConnectionFactory.get_session()
        yield session
        session.close()
    
    @pytest.fixture
    def conversation_repo(self, db_session):
        """
        Create a conversation repository.
        """
        return ConversationRepository(db_session)
    
    @pytest.fixture
    def context_service(self, db_session):
        """
        Create a context service.
        """
        return ContextService(db_session)
    
    @pytest.fixture
    def test_user_id(self):
        """
        Create a test user ID.
        """
        return 1  # Assuming user ID 1 exists in the test database
    
    @pytest.fixture
    def test_conversation(self, conversation_repo, test_user_id):
        """
        Create a test conversation.
        """
        # Create conversation
        conversation = conversation_repo.create(
            user_id=test_user_id,
            title="Performance Test Conversation",
            agent_type=AgentType.DOCUMENTATION
        )
        
        # Return conversation
        yield conversation
        
        # Clean up
        conversation_repo.delete_conversation(conversation.conversation_id)
    
    def generate_random_text(self, length: int = 100) -> str:
        """
        Generate random text for testing.
        
        Args:
            length: Length of text to generate
            
        Returns:
            str: Random text
        """
        words = []
        for _ in range(length // 5):  # Average word length of 5
            word_length = random.randint(3, 10)
            word = ''.join(random.choice(string.ascii_lowercase) for _ in range(word_length))
            words.append(word)
        return ' '.join(words)
    
    def test_add_message_performance(self, conversation_repo, test_conversation):
        """
        Test performance of adding messages to a conversation.
        """
        # Number of messages to add
        num_messages = 100
        
        # Measure time to add messages
        start_time = time.time()
        
        for i in range(num_messages):
            role = MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT
            content = self.generate_random_text(200)  # 200 characters per message
            
            message = conversation_repo.add_message(
                conversation_id=test_conversation.conversation_id,
                role=role,
                content=content,
                add_to_context=True,
                extract_preferences=False  # Disable for performance testing
            )
            assert message is not None
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # Log performance metrics
        print(f"\nPerformance metrics for adding {num_messages} messages:")
        print(f"Total time: {elapsed_time:.2f} seconds")
        print(f"Average time per message: {(elapsed_time / num_messages) * 1000:.2f} ms")
        
        # Assert reasonable performance
        # This is a flexible threshold that may need adjustment based on the environment
        assert elapsed_time / num_messages < 0.1  # Less than 100ms per message
    
    def test_context_retrieval_performance(self, conversation_repo, test_conversation):
        """
        Test performance of retrieving context for a conversation.
        """
        # Add messages to the conversation
        num_messages = 50
        for i in range(num_messages):
            role = MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT
            content = self.generate_random_text(200)  # 200 characters per message
            
            message = conversation_repo.add_message(
                conversation_id=test_conversation.conversation_id,
                role=role,
                content=content,
                add_to_context=True,
                extract_preferences=False  # Disable for performance testing
            )
            assert message is not None
        
        # Measure time to retrieve context
        num_retrievals = 10
        total_time = 0
        
        for _ in range(num_retrievals):
            start_time = time.time()
            
            context = conversation_repo.get_conversation_context(
                conversation_id=test_conversation.conversation_id,
                max_tokens=4000,
                include_system_prompt=True
            )
            
            end_time = time.time()
            total_time += (end_time - start_time)
            
            assert len(context) > 0
        
        average_time = total_time / num_retrievals
        
        # Log performance metrics
        print(f"\nPerformance metrics for retrieving context ({num_messages} messages):")
        print(f"Average retrieval time: {average_time * 1000:.2f} ms")
        
        # Assert reasonable performance
        # This is a flexible threshold that may need adjustment based on the environment
        assert average_time < 0.5  # Less than 500ms per retrieval
    
    def test_pruning_performance(self, conversation_repo, context_service, test_conversation):
        """
        Test performance of pruning context.
        """
        # Add messages to the conversation
        num_messages = 100
        for i in range(num_messages):
            role = MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT
            content = self.generate_random_text(200)  # 200 characters per message
            
            message = conversation_repo.add_message(
                conversation_id=test_conversation.conversation_id,
                role=role,
                content=content,
                add_to_context=True,
                extract_preferences=False  # Disable for performance testing
            )
            assert message is not None
        
        # Get context window
        window_repo = ContextWindowRepository(context_service.session)
        window = window_repo.get_active_window_for_conversation(test_conversation.id)
        assert window is not None
        
        # Get context items
        item_repo = ContextItemRepository(context_service.session)
        items = item_repo.get_items_for_window(window.id, included_only=True)
        assert len(items) >= num_messages
        
        # Test different pruning strategies
        pruning_strategies = [
            ("PriorityBasedPruning", PriorityBasedPruning()),
            ("RelevanceBasedPruning", RelevanceBasedPruning()),
            ("TimeBasedPruning", TimeBasedPruning()),
            ("HybridPruningStrategy", HybridPruningStrategy([
                PriorityBasedPruning(),
                RelevanceBasedPruning(),
                TimeBasedPruning()
            ]))
        ]
        
        print("\nPruning performance metrics:")
        
        for name, strategy in pruning_strategies:
            # Reset window and items
            window = window_repo.get_active_window_for_conversation(test_conversation.id)
            items = item_repo.get_items_for_window(window.id, included_only=True)
            
            # Measure pruning time
            start_time = time.time()
            
            success = strategy.prune(
                window=window,
                items=items,
                max_tokens=2000,  # Force pruning
                item_repo=item_repo,
                window_repo=window_repo
            )
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            assert success is True
            
            # Get updated window and items
            window = window_repo.get_active_window_for_conversation(test_conversation.id)
            items_after = item_repo.get_items_for_window(window.id, included_only=True)
            
            # Log performance metrics
            print(f"{name}:")
            print(f"  Time: {elapsed_time * 1000:.2f} ms")
            print(f"  Items before: {len(items)}")
            print(f"  Items after: {len(items_after)}")
            print(f"  Items pruned: {len(items) - len(items_after)}")
            
            # Assert reasonable performance
            # This is a flexible threshold that may need adjustment based on the environment
            assert elapsed_time < 1.0  # Less than 1 second for pruning
    
    def test_concurrent_context_operations(self, conversation_repo, test_conversation):
        """
        Test performance of concurrent context operations.
        """
        import threading
        
        # Number of concurrent operations
        num_threads = 10
        num_operations_per_thread = 10
        
        # Create threads
        threads = []
        errors = []
        
        def add_messages():
            try:
                for i in range(num_operations_per_thread):
                    role = MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT
                    content = self.generate_random_text(100)  # 100 characters per message
                    
                    message = conversation_repo.add_message(
                        conversation_id=test_conversation.conversation_id,
                        role=role,
                        content=content,
                        add_to_context=True,
                        extract_preferences=False  # Disable for performance testing
                    )
                    assert message is not None
            except Exception as e:
                errors.append(str(e))
        
        # Start threads
        start_time = time.time()
        
        for _ in range(num_threads):
            thread = threading.Thread(target=add_messages)
            threads.append(thread)
            thread.start()
        
        # Wait for threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # Log performance metrics
        total_operations = num_threads * num_operations_per_thread
        print(f"\nConcurrent operations performance metrics:")
        print(f"Total operations: {total_operations}")
        print(f"Total time: {elapsed_time:.2f} seconds")
        print(f"Operations per second: {total_operations / elapsed_time:.2f}")
        
        # Check for errors
        assert len(errors) == 0, f"Errors occurred during concurrent operations: {errors}"
        
        # Assert reasonable performance
        # This is a flexible threshold that may need adjustment based on the environment
        assert elapsed_time / total_operations < 0.1  # Less than 100ms per operation
