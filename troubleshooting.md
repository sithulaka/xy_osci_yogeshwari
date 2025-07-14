# Troubleshooting Guide

## Common Issues and Solutions

### 1. Python Service Won't Start

**Problem**: `sudo systemctl start key-detector.service` fails

**Solutions**:
```bash
# Check service status
sudo systemctl status key-detector.service

# View detailed logs
sudo journalctl -u key-detector.service -f

# Common fixes:
# 1. Install missing dependencies
pip3 install websockets pynput

# 2. Check Python path
which python3

# 3. Test manually first
cd /home/kavinda/Desktop/work/xy/xy_osci_yogeshwari
python3 key_detector.py
```

### 2. Permission Denied Errors

**Problem**: Web files or service can't access files

**Solutions**:
```bash
# Fix web directory permissions
sudo chown -R www-data:www-data /var/www/kuweni
sudo chmod -R 755 /var/www/kuweni

# Fix service file permissions
sudo chown root:root /etc/systemd/system/key-detector.service
sudo chmod 644 /etc/systemd/system/key-detector.service
```

### 3. WebSocket Connection Failed

**Problem**: Browser console shows "WebSocket connection failed"

**Solutions**:
```bash
# Check if service is running
sudo systemctl status key-detector.service

# Check if port 8765 is open
netstat -tlnp | grep 8765

# Test WebSocket manually
python3 -c "
import asyncio
import websockets

async def test():
    try:
        async with websockets.connect('ws://localhost:8765') as websocket:
            print('Connection successful')
    except Exception as e:
        print(f'Connection failed: {e}')

asyncio.run(test())
"
```

### 4. Audio Files Not Loading

**Problem**: Browser shows "Failed to load audio files"

**Solutions**:
```bash
# Check if audio files exist
ls -la /var/www/kuweni/audio/

# Check audio-config.json
cat /var/www/kuweni/audio-config.json

# Test audio file access
curl http://localhost/kuweni/audio/Asset\ 2.wav
```

### 5. Web Server Issues

**Problem**: Can't access http://localhost/kuweni/

**Solutions**:

**For Apache**:
```bash
# Check if Apache is running
sudo systemctl status apache2

# Check site configuration
sudo apache2ctl configtest

# Enable site
sudo a2ensite kuweni
sudo systemctl reload apache2
```

**For Nginx**:
```bash
# Check if Nginx is running
sudo systemctl status nginx

# Test configuration
sudo nginx -t

# Enable site
sudo ln -s /etc/nginx/sites-available/kuweni /etc/nginx/sites-enabled/
sudo systemctl reload nginx
```

### 6. Key Detection Not Working

**Problem**: Pressing keys doesn't trigger audio

**Solutions**:
```bash
# Check if pynput has proper permissions
# On some systems, you may need to run as root or add user to input group
sudo usermod -a -G input $USER

# For X11 systems, ensure DISPLAY is set
export DISPLAY=:0

# Test key detection manually
python3 -c "
from pynput import keyboard
def on_press(key):
    print(f'Key pressed: {key}')
listener = keyboard.Listener(on_press=on_press)
listener.start()
listener.join()
"
```

### 7. Service Logs and Debugging

**Useful commands**:
```bash
# Real-time logs
sudo journalctl -u key-detector.service -f

# Last 50 lines of logs
sudo journalctl -u key-detector.service -n 50

# Restart service
sudo systemctl restart key-detector.service

# Stop service
sudo systemctl stop key-detector.service

# Check service file syntax
sudo systemctl daemon-reload
```

### 8. Browser Console Errors

**Common browser errors and fixes**:

1. **"Keyboard audio manager failed to initialize"**
   - Check if WebSocket service is running
   - Verify audio-config.json is accessible

2. **"Failed to load audio files"**
   - Check audio file paths in audio-config.json
   - Verify web server can serve audio files

3. **"WebGL context lost"**
   - Refresh the page
   - Check browser WebGL support

### 9. Performance Issues

**If oscilloscope is slow or laggy**:
```bash
# Check system resources
htop

# Check service resource usage
sudo systemctl status key-detector.service

# Reduce buffer size in oscilloscope.js if needed
# Look for: AudioSystem.init(1024); and try AudioSystem.init(512);
```

### 10. Complete Reset

**If nothing works, try a complete reset**:
```bash
# Stop service
sudo systemctl stop key-detector.service
sudo systemctl disable key-detector.service

# Remove service file
sudo rm /etc/systemd/system/key-detector.service

# Remove web files
sudo rm -rf /var/www/kuweni

# Reload systemd
sudo systemctl daemon-reload

# Start fresh with deploy.sh
./deploy.sh
```