#!/usr/bin/env python
"""
Database initialization script for MAGPIE platform.

This script:
1. Creates the database if it doesn't exist
2. Runs Alembic migrations to create the schema
3. Creates seed data for testing

Usage:
    python scripts/init_db.py [--reset] [--seed]

Options:
    --reset     Drop and recreate the database
    --seed      Create seed data
"""
import argparse
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add the project root directory to the Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import alembic.config
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError, OperationalError
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.models.agent import AgentConfiguration


def create_database(reset=False):
    """
    Create the database if it doesn't exist.

    Args:
        reset: If True, drop and recreate the database
    """
    # Extract database name from URL
    db_url_parts = settings.DATABASE_URL.split('/')
    db_name = db_url_parts[-1]

    # Create connection URL to postgres database
    postgres_url = '/'.join(db_url_parts[:-1] + ['postgres'])

    # Connect to postgres database
    engine = create_engine(postgres_url)
    conn = engine.connect()
    conn.execution_options(isolation_level="AUTOCOMMIT")

    try:
        if reset:
            print(f"Dropping database '{db_name}'...")
            conn.execute(text(f'DROP DATABASE IF EXISTS {db_name}'))

        # Check if database exists
        result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
        exists = result.scalar() == 1

        if not exists:
            print(f"Creating database '{db_name}'...")
            conn.execute(text(f'CREATE DATABASE {db_name}'))
            print(f"Database '{db_name}' created successfully.")
        else:
            print(f"Database '{db_name}' already exists.")
    except (ProgrammingError, OperationalError) as e:
        print(f"Error creating database: {str(e)}")
    finally:
        conn.close()
        engine.dispose()


def run_migrations():
    """
    Run Alembic migrations to create the schema.
    """
    print("Running database migrations...")
    alembic_args = [
        '--raiseerr',
        'upgrade', 'head',
    ]
    alembic.config.main(argv=alembic_args)
    print("Database migrations completed successfully.")


def create_seed_data():
    """
    Create seed data for testing.
    """
    print("Creating seed data...")

    # Create database engine
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Create admin user
        admin_user = User(
            email="admin@magpie.com",
            username="admin",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password"
            full_name="Admin User",
            role="admin",  # Use string value instead of enum
            is_active=True,
            is_superuser=True
        )
        session.add(admin_user)

        # Create engineer user
        engineer_user = User(
            email="engineer@magpie.com",
            username="engineer",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password"
            full_name="Engineer User",
            role="engineer",  # Use string value instead of enum
            is_active=True,
            is_superuser=False
        )
        session.add(engineer_user)

        # Create technician user
        technician_user = User(
            email="technician@magpie.com",
            username="technician",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password"
            full_name="Technician User",
            role="technician",  # Use string value instead of enum
            is_active=True,
            is_superuser=False
        )
        session.add(technician_user)

        # Flush to get user IDs
        session.flush()

        # Create agent configurations
        documentation_agent = AgentConfiguration(
            name="Default Documentation Assistant",
            description="Default configuration for the documentation assistant",
            agent_type="documentation",  # Use string value instead of enum
            model_size="medium",  # Use string value instead of enum
            temperature=0.7,
            max_tokens=4000,
            system_prompt="You are a helpful aircraft maintenance documentation assistant. Your role is to help technicians and engineers find relevant information in technical documentation.",
            is_active=True,
            meta_data={"is_default": True}
        )
        session.add(documentation_agent)

        troubleshooting_agent = AgentConfiguration(
            name="Default Troubleshooting Advisor",
            description="Default configuration for the troubleshooting advisor",
            agent_type="troubleshooting",  # Use string value instead of enum
            model_size="large",  # Use string value instead of enum
            temperature=0.5,
            max_tokens=8000,
            system_prompt="You are a helpful aircraft troubleshooting advisor. Your role is to help technicians and engineers diagnose and resolve issues with aircraft systems.",
            is_active=True,
            meta_data={"is_default": True}
        )
        session.add(troubleshooting_agent)

        maintenance_agent = AgentConfiguration(
            name="Default Maintenance Procedure Generator",
            description="Default configuration for the maintenance procedure generator",
            agent_type="maintenance",  # Use string value instead of enum
            model_size="large",  # Use string value instead of enum
            temperature=0.3,
            max_tokens=8000,
            system_prompt="You are a helpful aircraft maintenance procedure generator. Your role is to help technicians and engineers create step-by-step maintenance procedures based on technical documentation.",
            is_active=True,
            meta_data={"is_default": True}
        )
        session.add(maintenance_agent)

        # Flush to get agent IDs
        session.flush()

        # Create conversations
        documentation_conversation = Conversation(
            conversation_id=uuid.uuid4(),
            title="Boeing 737 MAX Documentation",
            user_id=engineer_user.id,
            agent_type="documentation",  # Use string value instead of enum
            is_active=True
        )
        session.add(documentation_conversation)

        troubleshooting_conversation = Conversation(
            conversation_id=uuid.uuid4(),
            title="Airbus A320 Hydraulic System Issue",
            user_id=technician_user.id,
            agent_type="troubleshooting",  # Use string value instead of enum
            is_active=True
        )
        session.add(troubleshooting_conversation)

        # Flush to get conversation IDs
        session.flush()

        # Create messages for documentation conversation
        documentation_messages = [
            Message(
                conversation_id=documentation_conversation.id,
                role="system",  # Use string value instead of enum
                content="You are a helpful aircraft maintenance documentation assistant. Your role is to help technicians and engineers find relevant information in technical documentation."
            ),
            Message(
                conversation_id=documentation_conversation.id,
                role="user",  # Use string value instead of enum
                content="I need information about the Boeing 737 MAX flight control system."
            ),
            Message(
                conversation_id=documentation_conversation.id,
                role="assistant",  # Use string value instead of enum
                content="The Boeing 737 MAX flight control system includes the Maneuvering Characteristics Augmentation System (MCAS), which is designed to enhance pitch stability at high angles of attack. Here are the key components and characteristics:\n\n1. MCAS Function: Automatically adjusts the horizontal stabilizer to push the nose down when the aircraft is operating at high angles of attack\n\n2. Activation Conditions: Activates when the aircraft is in manual flight (autopilot off), at high angle of attack, and with flaps retracted\n\n3. Sensors: Uses data from angle of attack (AOA) sensors\n\n4. Control: Moves the horizontal stabilizer via the trim system\n\nWould you like more specific information about any particular aspect of the flight control system?"
            )
        ]
        session.add_all(documentation_messages)

        # Create messages for troubleshooting conversation
        troubleshooting_messages = [
            Message(
                conversation_id=troubleshooting_conversation.id,
                role="system",  # Use string value instead of enum
                content="You are a helpful aircraft troubleshooting advisor. Your role is to help technicians and engineers diagnose and resolve issues with aircraft systems."
            ),
            Message(
                conversation_id=troubleshooting_conversation.id,
                role="user",  # Use string value instead of enum
                content="I'm getting a hydraulic system pressure warning on an Airbus A320. What should I check first?"
            ),
            Message(
                conversation_id=troubleshooting_conversation.id,
                role="assistant",  # Use string value instead of enum
                content="For an Airbus A320 hydraulic system pressure warning, here's a systematic approach to troubleshooting:\n\n1. First, check the hydraulic fluid levels in all three systems (Green, Yellow, and Blue). Low fluid level is the most common cause of pressure warnings.\n\n2. Inspect for visible hydraulic leaks around the main hydraulic reservoirs, pumps, and major hydraulic lines.\n\n3. Check the status of hydraulic pumps:\n   - Engine-driven pumps (Green system from Engine 1, Yellow from Engine 2)\n   - Electric pumps (Yellow and Blue systems)\n   - RAT (Ram Air Turbine) pump if deployed (Yellow system)\n\n4. Verify circuit breakers related to the hydraulic system haven't tripped.\n\n5. Check the ECAM (Electronic Centralized Aircraft Monitor) for specific fault codes that might provide more detailed information.\n\nWhich hydraulic system is showing the pressure warning (Green, Yellow, or Blue)?"
            ),
            Message(
                conversation_id=troubleshooting_conversation.id,
                role="user",  # Use string value instead of enum
                content="It's the Green system."
            ),
            Message(
                conversation_id=troubleshooting_conversation.id,
                role="assistant",  # Use string value instead of enum
                content="Since it's the Green hydraulic system showing a pressure warning on the A320, focus your troubleshooting on these specific areas:\n\n1. Green System Specifics:\n   - The Green system is primarily powered by the Engine 1 (left engine) driven pump\n   - Normal pressure should be 3000 psi (207 bar)\n   - Low pressure warning activates below approximately 1700 psi (117 bar)\n\n2. Check Engine 1 Status:\n   - Verify Engine 1 is running at proper N2 speed\n   - The engine-driven pump won't provide pressure if the engine is not running or at low RPM\n\n3. Inspect the Green System Reservoir:\n   - Check fluid level in the Green hydraulic reservoir (located in the lower fuselage)\n   - Verify proper pressurization of the reservoir\n\n4. Check for Leaks in Green System Components:\n   - Engine 1 hydraulic pump and connections\n   - Main landing gear actuators (Green system powers these)\n   - Cargo door actuators\n   - Thrust reverser actuators for Engine 1\n\n5. Inspect the Fire Shut-Off Valve:\n   - Ensure the Engine 1 fire shut-off valve is not activated, as this would cut hydraulic flow\n\n6. Check System Isolation:\n   - Verify the Green system isolation valve is in the correct position\n\nWould you like me to provide the specific maintenance manual references for any of these checks?"
            )
        ]
        session.add_all(troubleshooting_messages)

        # Commit changes
        session.commit()
        print("Seed data created successfully.")
    except Exception as e:
        session.rollback()
        print(f"Error creating seed data: {str(e)}")
    finally:
        session.close()
        engine.dispose()


def main():
    """
    Main function.
    """
    parser = argparse.ArgumentParser(description="Initialize the MAGPIE database")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate the database")
    parser.add_argument("--seed", action="store_true", help="Create seed data")
    args = parser.parse_args()

    # Create database
    create_database(reset=args.reset)

    # Run migrations
    run_migrations()

    # Create seed data if requested
    if args.seed:
        create_seed_data()

    print("Database initialization completed successfully.")


if __name__ == "__main__":
    main()
