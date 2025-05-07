/**
 * WebSocket Test Script
 * 
 * This script tests the WebSocket connection to the backend.
 * Run it with: npx ts-node -r tsconfig-paths/register src/scripts/test-websocket.ts
 */

import WebSocket from 'ws';

// WebSocket URL
const WS_URL = 'ws://localhost:8000/ws';

// Test user ID
const USER_ID = 'test-user';

// Test conversation ID
const CONVERSATION_ID = 'test-conversation';

// Connect to WebSocket
console.log(`Connecting to WebSocket at ${WS_URL}...`);
const socket = new WebSocket(`${WS_URL}?user_id=${USER_ID}&conversation_id=${CONVERSATION_ID}`);

// Handle open event
socket.on('open', () => {
  console.log('WebSocket connection established');
  
  // Send a test message
  const message = {
    type: 'message',
    payload: {
      message: 'Hello from WebSocket test script',
      conversation_id: CONVERSATION_ID
    }
  };
  
  console.log('Sending message:', message);
  socket.send(JSON.stringify(message));
});

// Handle message event
socket.on('message', (data) => {
  try {
    const message = JSON.parse(data.toString());
    console.log('Received message:', message);
    
    // If this is a welcome message, we're done
    if (message.type === 'connection' && message.payload.status === 'connected') {
      console.log('Connection confirmed');
    }
    
    // If this is a response to our message, close the connection
    if (message.type === 'message' && message.payload.message) {
      console.log('Received response, closing connection');
      socket.close();
    }
  } catch (error) {
    console.error('Error parsing message:', error);
  }
});

// Handle error event
socket.on('error', (error) => {
  console.error('WebSocket error:', error);
});

// Handle close event
socket.on('close', (code, reason) => {
  console.log(`WebSocket connection closed: ${code} ${reason}`);
  process.exit(0);
});

// Close the connection after 10 seconds if no response
setTimeout(() => {
  if (socket.readyState === WebSocket.OPEN) {
    console.log('No response received, closing connection');
    socket.close();
    process.exit(1);
  }
}, 10000);
