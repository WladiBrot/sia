[Unit]
Description=Raspberry Pi Kamera beim Startup ausführen
After=multi-user.target

[Service]
Type=idle
ExecStart=/usr/bin/python3 /home/pi/camera_startup.py
Restart=on-failure
User=pi

[Install]
WantedBy=multi-user.target
