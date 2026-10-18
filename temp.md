Option 1: usbipd-win (pass the webcam through to WSL2)

On Windows (PowerShell as Administrator):

powershell
winget install --interactive --exact dorssel.usbipd-win

Restart PowerShell, then:

powershell
usbipd list

Find your webcam’s BUSID (e.g. 2-4), then:

powershell
usbipd bind --busid 2-4
usbipd attach --wsl --busid 2-4

In WSL:

bash
ls /dev/video*

If nothing shows up, your WSL2 kernel probably lacks the UVC/V4L2 drivers. Check:

bash
zcat /proc/config.gz | grep -E "VIDEO_V4L2|USB_VIDEO_CLASS"

If they’re missing, you need a custom kernel (build Microsoft’s WSL2-Linux-Kernel with CONFIG_MEDIA_SUPPORT, CONFIG_VIDEO_V4L2, CONFIG_USB_VIDEO_CLASS enabled, then point .wslconfig at it with kernel=C:\\path\\to\\bzImage). Newer WSL kernel versions (6.6+) may already include some of these, so check first with uname -r and wsl --update.

Once /dev/video0 exists, you may need:

bash
sudo usermod -aG video $USER