# Setup Instructions for XY Oscilloscope

## 1. Copy Web Files to /var/www/kuweni

```bash
# Create the directory
sudo mkdir -p /var/www/kuweni

# Copy all web files
sudo cp -r /home/kavinda/Desktop/work/xy/xy_osci_yogeshwari/web/* /var/www/kuweni/

# Copy audio files
sudo cp -r /home/kavinda/Desktop/work/xy/xy_osci_yogeshwari/audio /var/www/kuweni/

# Set proper permissions
sudo chown -R www-data:www-data /var/www/kuweni
sudo chmod -R 755 /var/www/kuweni
```

## 2. Create Python Key Detector Service

Create service file: `/etc/systemd/system/key-detector.service`

```ini
[Unit]
Description=XY Oscilloscope Key Detector
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/kavinda/Desktop/work/xy/xy_osci_yogeshwari
ExecStart=/usr/bin/python3 key_detector.py
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

## 3. Service Management Commands

```bash
# Enable and start the service
sudo systemctl enable key-detector.service
sudo systemctl start key-detector.service

# Check service status
sudo systemctl status key-detector.service

# View logs
sudo journalctl -u key-detector.service -f

# Stop/restart service
sudo systemctl stop key-detector.service
sudo systemctl restart key-detector.service
```

## 4. Web Server Configuration

### For Apache:
Create `/etc/apache2/sites-available/kuweni.conf`:

```apache
<VirtualHost *:80>
    ServerName localhost
    DocumentRoot /var/www/kuweni
    
    <Directory /var/www/kuweni>
        Options Indexes FollowSymLinks
        AllowOverride None
        Require all granted
    </Directory>
    
    ErrorLog ${APACHE_LOG_DIR}/kuweni_error.log
    CustomLog ${APACHE_LOG_DIR}/kuweni_access.log combined
</VirtualHost>
```

Enable site:
```bash
sudo a2ensite kuweni
sudo systemctl reload apache2
```

### For Nginx:
Create `/etc/nginx/sites-available/kuweni`:

```nginx
server {
    listen 80;
    server_name localhost;
    
    root /var/www/kuweni;
    index index.html;
    
    location / {
        try_files $uri $uri/ =404;
    }
    
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/kuweni /etc/nginx/sites-enabled/
sudo systemctl reload nginx
```

## 5. Troubleshooting

### Common Issues:

1. **Permission Denied**: Make sure www-data owns the files
2. **Service Won't Start**: Check Python path and dependencies
3. **WebSocket Connection Failed**: Ensure key_detector.py is running on port 8765
4. **Audio Files Not Loading**: Check file paths in audio-config.json

### Debug Commands:

```bash
# Check if Python service is running
sudo systemctl status key-detector.service

# Check if web server is running
sudo systemctl status apache2  # or nginx

# Check WebSocket connection
netstat -tlnp | grep 8765

# Test web server
curl http://localhost/kuweni/
```

## 6. Dependencies

Make sure these are installed:
```bash
sudo apt update
sudo apt install python3 python3-pip apache2  # or nginx
pip3 install websockets pynput
```