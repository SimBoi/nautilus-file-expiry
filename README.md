> [!WARNING]
> This repo is no longer maintained.

![image](https://github.com/user-attachments/assets/8f887e19-e889-4224-bb92-ce9810ad9a04)

# File Expiry For Nautilus

An extension for Nautilus. Adds file expiration support to the right-click menu, schedule files to be automatically deleted at a later time.

- Uses both the file path and its inode to verify its the correct file for deletion, meaning that renaming/moving/recreating the file will cancel its expiration.
- Moves expired files to the trash
- Expiry can either be scheduled or set to a specific period of no use
- Expiry status can be viewed and cancelled

Check my [nautilus extension collection](https://github.com/SimBoi/nautilus-extension-collection).

## 🚀 Installation

1. Install required packages
	```bash
	# Debian
	sudo apt update
	sudo apt install -y git curl python3-nautilus at
	```
	```bash
	# Arch
	sudo pacman -Syy
	sudo pacman -S git curl nautilus-python at
	```
	```bash
	# Fedora
	sudo dnf update
	sudo dnf install -y git curl nautilus-python at
	```
2. Install the scripts
	```bash
	mkdir -p ~/.local/share/nautilus-python/extensions
	curl -L -o ~/.local/share/nautilus-python/extensions/nautilus-file-expiry.py https://raw.githubusercontent.com/simboi/nautilus-file-expiry/main/nautilus-file-expiry.py
	sudo mkdir -p /opt/file-expiry/
	sudo curl -L -o /opt/file-expiry/delete-if-inode-matches.sh https://raw.githubusercontent.com/simboi/nautilus-file-expiry/main/delete-if-inode-matches.sh
	sudo chmod +x /opt/file-expiry/delete-if-inode-matches.sh
	```
3. Restart nautilus
	```bash
	nautilus -q
	```
4. Profit

## 🗑️ Uninstallation

1. Run in the terminal:
	```bash
	rm -f ~/.local/share/nautilus-python/extensions/nautilus-open-in-vscode.py
	curl -fsSL https://raw.githubusercontent.com/SimBoi/nautilus-create-new-file/main/uninstall.sh | bash
	rm -f ~/.local/share/nautilus-python/extensions/nautilus-git-operations.py
 	rm -f ~/.local/share/nautilus-python/extensions/nautilus-more-copy.py
 	rm -f ~/.local/share/nautilus-python/extensions/nautilus-regex-select.py
 	sudo rm -rf /opt/file-expiry
 	```
2. Restart Nautilus
	```bash
	nautilus -q
	````
3. Unprofit

