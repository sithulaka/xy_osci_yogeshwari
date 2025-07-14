#!/usr/bin/env python3
"""
Hardware Key Press Detection for Oscilloscope
Detects key presses using Python and sends them to the web application via WebSocket
"""

import asyncio
import json
import logging
import websockets
from pynput import keyboard
import threading
import queue
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KeyDetector:
    def __init__(self):
        self.key_mappings = {
            'a': 'a', 's': 's', 'd': 'd', 'f': 'f', 'g': 'g', 'h': 'h',
            'j': 'j', 'k': 'k', 'l': 'l', 'q': 'q', 'w': 'w', 'e': 'e',
            'r': 'r', 't': 't', 'y': 'y', 'u': 'u', 'i': 'i', 'o': 'o',
            'p': 'p', 'z': 'z'
        }
        self.pressed_keys = set()
        self.key_queue = queue.Queue()
        self.connected_clients = set()
        self.running = False
        
    def on_key_press(self, key):
        """Handle key press events"""
        try:
            # Convert key to string
            if hasattr(key, 'char') and key.char:
                key_char = key.char.lower()
            else:
                # Handle special keys
                key_char = str(key).replace('Key.', '')
                
            # Check if this key is in our mappings and not already pressed
            if key_char in self.key_mappings and key_char not in self.pressed_keys:
                self.pressed_keys.add(key_char)
                self.key_queue.put(('keydown', key_char))
                logger.info(f"Key pressed: {key_char}")
                
        except Exception as e:
            logger.error(f"Error handling key press: {e}")
    
    def on_key_release(self, key):
        """Handle key release events"""
        try:
            # Convert key to string
            if hasattr(key, 'char') and key.char:
                key_char = key.char.lower()
            else:
                # Handle special keys
                key_char = str(key).replace('Key.', '')
                
            # Check if this key was pressed and is in our mappings
            if key_char in self.key_mappings and key_char in self.pressed_keys:
                self.pressed_keys.remove(key_char)
                self.key_queue.put(('keyup', key_char))
                logger.info(f"Key released: {key_char}")
                
        except Exception as e:
            logger.error(f"Error handling key release: {e}")
    
    def start_key_listener(self):
        """Start the keyboard listener in a separate thread"""
        def listen():
            with keyboard.Listener(
                on_press=self.on_key_press,
                on_release=self.on_key_release
            ) as listener:
                logger.info("Keyboard listener started")
                listener.join()
        
        listener_thread = threading.Thread(target=listen, daemon=True)
        listener_thread.start()
        return listener_thread
    
    async def handle_client(self, websocket, path):
        """Handle WebSocket client connections"""
        logger.info(f"Client connected: {websocket.remote_address}")
        self.connected_clients.add(websocket)
        
        try:
            # Send current state to new client
            await websocket.send(json.dumps({
                'type': 'status',
                'pressed_keys': list(self.pressed_keys),
                'key_mappings': self.key_mappings
            }))
            
            # Keep connection alive
            async for message in websocket:
                # Handle incoming messages if needed
                data = json.loads(message)
                if data.get('type') == 'ping':
                    await websocket.send(json.dumps({'type': 'pong'}))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {websocket.remote_address}")
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            self.connected_clients.discard(websocket)
    
    async def broadcast_key_events(self):
        """Broadcast key events to all connected clients"""
        while self.running:
            try:
                # Get key event from queue (non-blocking)
                try:
                    event_type, key_char = self.key_queue.get_nowait()
                except queue.Empty:
                    await asyncio.sleep(0.01)  # Small delay to prevent busy waiting
                    continue
                
                # Broadcast to all connected clients
                if self.connected_clients:
                    message = json.dumps({
                        'type': event_type,
                        'key': key_char,
                        'timestamp': time.time()
                    })
                    
                    # Send to all clients
                    disconnected_clients = set()
                    for client in self.connected_clients:
                        try:
                            await client.send(message)
                        except websockets.exceptions.ConnectionClosed:
                            disconnected_clients.add(client)
                        except Exception as e:
                            logger.error(f"Error sending to client: {e}")
                            disconnected_clients.add(client)
                    
                    # Remove disconnected clients
                    self.connected_clients -= disconnected_clients
                    
            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
                await asyncio.sleep(0.1)
    
    async def start_server(self, host='localhost', port=8765):
        """Start the WebSocket server"""
        logger.info(f"Starting WebSocket server on {host}:{port}")
        
        # Start keyboard listener
        self.start_key_listener()
        
        # Start the server and broadcast task
        self.running = True
        
        server = await websockets.serve(self.handle_client, host, port)
        broadcast_task = asyncio.create_task(self.broadcast_key_events())
        
        logger.info("Key detector server ready!")
        logger.info("Press keys to send events to connected clients")
        logger.info("Press Ctrl+C to stop")
        
        try:
            await asyncio.Future()  # Run forever
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            self.running = False
            broadcast_task.cancel()
            server.close()
            await server.wait_closed()

def main():
    """Main function"""
    try:
        # Check for required dependencies
        import pynput
        import websockets
    except ImportError as e:
        logger.error(f"Missing required dependency: {e}")
        logger.error("Please install dependencies: pip install -r requirements.txt")
        return
    
    detector = KeyDetector()
    
    try:
        asyncio.run(detector.start_server())
    except KeyboardInterrupt:
        logger.info("Stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    main()