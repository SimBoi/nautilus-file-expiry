from typing import List
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import GObject, Adw, Gtk, Nautilus


# shows an alert dialog with a heading and body text to the user
def message_alert(heading: str, body: str, dismiss_label: str = 'Dismiss', parent: Adw.Dialog = None):
    dialog = Adw.AlertDialog(
            heading=heading,
            body=body,
        )
    dialog.add_response(
            id=dismiss_label,
            label=dismiss_label,
        )
    dialog.present(parent)

def schedule_file_expiry_at(path: str, at_time: str):
    import subprocess, shlex, os
    cmd = f"/opt/file-expiry/delete-if-inode-matches.sh {shlex.quote(path)} {os.stat(path).st_ino}"
    subprocess.run(['bash', '-c', f'echo {shlex.quote(cmd)} | at {at_time}'], check=True)

def schedule_file_expiry_after(path: str, expire_after: int):
    import subprocess, shlex, os
    cmd = f"/opt/file-expiry/delete-if-inode-matches.sh {shlex.quote(path)} {os.stat(path).st_ino} {expire_after}"
    subprocess.run(['bash', '-c', f'echo {shlex.quote(cmd)} | at now + {expire_after} minutes'], check=True)

def cancel_file_expiry(path: str):
    import subprocess, shlex, os
    atq = subprocess.check_output(['atq']).decode().splitlines()
    for job in atq:
        job_id = job.split()[0]
        try:
            output = subprocess.check_output(['at', '-c', job_id]).decode()
            if f"/opt/file-expiry/delete-if-inode-matches.sh {shlex.quote(path)} {os.stat(path).st_ino}" in output:
                subprocess.run(['atrm', job_id], check=True)
        except:
            continue

def get_file_expiry(path: str):
    import subprocess, shlex, os
    atq = subprocess.check_output(['atq']).decode().splitlines()
    for job in atq:
        parts = job.split()
        job_id = parts[0]
        # The time string is everything after the job id up to (but not including) the username at the end
        # Typically last two parts are username and queue letter, so exclude last two parts
        time_str = ' '.join(parts[1:-2])
        try:
            output = subprocess.check_output(['at', '-c', job_id]).decode()
            if f'/opt/file-expiry/delete-if-inode-matches.sh {shlex.quote(path)} {os.stat(path).st_ino}' in output:
                return time_str
        except:
            continue
    return None  # No expiry scheduled for this file


class FileExpiryDialog(Adw.Dialog):
    def __init__(self, file: Nautilus.FileInfo):
        super().__init__()

        self.file_path = file.get_location().get_path()

        # Set up the dialog properties
        self.set_title('File Expiry')
        self.set_content_width(450)
        root = Adw.ToolbarView()
        header_bar = Adw.HeaderBar()
        header_bar.set_decoration_layout(':close')
        root.add_top_bar (header_bar)
        body = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            hexpand=True,
            spacing=8,
            margin_top=16,
            margin_bottom=16,
            margin_start=16,
            margin_end=16,
        )
        root.set_content(body)
        list_box = Gtk.ListBox(css_classes=['boxed-list-separate'])
        body.append(list_box)

        # Create the entry for the absolute time string to pass to the linux 'at' command
        self.time_str_entry = Adw.EntryRow(title='Time String (\'at\' command format)')
        list_box.append(self.time_str_entry)

        # Create the entry for the expiry duration
        self.expiry_duration_entry = Adw.EntryRow(title='Expiry After (in minutes)')
        list_box.append(self.expiry_duration_entry)

        # Create the Submit button
        self.submit_button = Gtk.Button(
            label='Schedule Expiry',
            css_classes=['pill', 'suggested-action'],
            halign=Gtk.Align.CENTER,
            margin_top=8,
        )
        body.append(self.submit_button)
        def on_submit_clicked(*_):
            time_str = self.time_str_entry.get_text().strip()
            expiry_str = self.expiry_duration_entry.get_text().strip()
            if (time_str and expiry_str) or (not time_str and not expiry_str):
                message_alert(
                    heading="Input Error",
                    body="Please fill either 'Time String' or 'Expiry After', but not both.",
                    parent=self,
                )
                return
            if time_str:
                self.schedule_expiry_at()
            else:
                self.schedule_expiry_after()
        self.submit_button.connect(
            'clicked',
            on_submit_clicked,
            None,
        )

        self.set_child(root)

    def schedule_expiry_at(self):
        try:
            time_str = self.time_str_entry.get_text().strip()
            cancel_file_expiry(self.file_path)  # Cancel any existing expiry
            schedule_file_expiry_at(self.file_path, time_str)
            self.close()
        except Exception as e:
            message_alert(
                heading="Expiry Scheduling Error",
                body=f"Failed to schedule expiry: {e}",
                parent=self,
            )
            return

    def schedule_expiry_after(self):
        try:
            expire_after_str = self.expiry_duration_entry.get_text().strip()
            expire_after = int(expire_after_str)
            if not expire_after_str.isdigit() or expire_after <= 0:
                raise ValueError("Expiry After must be a positive integer.")
            cancel_file_expiry(self.file_path)  # Cancel any existing expiry
            schedule_file_expiry_after(self.file_path, expire_after)
            self.close()
        except Exception as e:
            message_alert(
                heading="Expiry Scheduling Error",
                body=f"Failed to schedule expiry: {e}",
                parent=self,
            )
            return


class FileExpiryProvider(GObject.GObject, Nautilus.MenuProvider):
    def get_file_items(
        self,
        files: List[Nautilus.FileInfo],
    ) -> List[Nautilus.MenuItem]:
        if not files or len(files) != 1:
            return []

        expiry_menu = Nautilus.Menu()
        expiry_time = get_file_expiry(files[0].get_location().get_path())

        if expiry_time is not None:
            expiry_status_item = Nautilus.MenuItem(
                name="FileExpiryProvider::ExpiryStatus",
                label="Expiry Status…",
            )
            expiry_status_item.connect(
                "activate",
                lambda *_: message_alert(
                    heading="File Expiry Status",
                    body=f"Expiry is scheduled for: {expiry_time}",
                ),
            )

            cancel_expiry_item = Nautilus.MenuItem(
                name="FileExpiryProvider::CancelExpiry",
                label="Cancel Expiry",
            )
            cancel_expiry_item.connect(
                "activate",
                lambda *_: self.cancel_expiry(files[0]),
            )

            expiry_menu.append_item(expiry_status_item)
            expiry_menu.append_item(cancel_expiry_item)
        else:
            in_one_hour_item = Nautilus.MenuItem(
                name="FileExpiryProvider::InOneHour",
                label="In One Hour",
            )
            in_one_hour_item.connect(
                "activate",
                lambda *_: self.schedule_expiry_at(files[0], "now + 1 hour"),
            )

            in_one_day_item = Nautilus.MenuItem(
                name="FileExpiryProvider::InOneDay",
                label="In One Day",
            )
            in_one_day_item.connect(
                "activate",
                lambda *_: self.schedule_expiry_at(files[0], "now + 1 day"),
            )

            in_one_week_item = Nautilus.MenuItem(
                name="FileExpiryProvider::InOneWeek",
                label="In One Week",
            )
            in_one_week_item.connect(
                "activate",
                lambda *_: self.schedule_expiry_at(files[0], "now + 1 week"),
            )

            in_one_month_item = Nautilus.MenuItem(
                name="FileExpiryProvider::InOneMonth",
                label="In One Month",
            )
            in_one_month_item.connect(
                "activate",
                lambda *_: self.schedule_expiry_at(files[0], "now + 1 month"),
            )

            after_one_week_item = Nautilus.MenuItem(
                name="FileExpiryProvider::AfterOneWeek",
                label="After One Week",
            )
            after_one_week_item.connect(
                "activate",
                lambda *_: self.schedule_expiry_after(files[0], 10080),  # 10080 minutes = 1 week
            )

            after_one_month_item = Nautilus.MenuItem(
                name="FileExpiryProvider::AfterOneMonth",
                label="After One Month",
            )
            after_one_month_item.connect(
                "activate",
                lambda *_: self.schedule_expiry_after(files[0], 43200),  # 43200 minutes = 1 month
            )

            custom_expiry_item = Nautilus.MenuItem(
                name="FileExpiryProvider::CustomExpiry",
                label="Custom Expiry…",
            )
            custom_expiry_item.connect(
                "activate",
                lambda *_: FileExpiryDialog(files[0]).present(),
            )

            expiry_menu.append_item(in_one_hour_item)
            expiry_menu.append_item(in_one_day_item)
            expiry_menu.append_item(in_one_week_item)
            expiry_menu.append_item(in_one_month_item)
            expiry_menu.append_item(after_one_week_item)
            expiry_menu.append_item(after_one_month_item)
            expiry_menu.append_item(custom_expiry_item)

        menu_item = Nautilus.MenuItem(
            name="FileExpiryProvider::ExpiryMenu",
            label="File Expiry",
        )
        menu_item.set_submenu(expiry_menu)
        return [menu_item]

    def cancel_expiry(self, file: Nautilus.FileInfo):
        try:
            cancel_file_expiry(file.get_location().get_path())
        except Exception as e:
            message_alert(
                heading="Expiry Cancellation Error",
                body=f"Failed to cancel expiry: {e}",
            )

    def schedule_expiry_at(self, file: Nautilus.FileInfo, time_str: str):
        try:
            schedule_file_expiry_at(file.get_location().get_path(), time_str)
        except Exception as e:
            message_alert(
                heading="Expiry Scheduling Error",
                body=f"Failed to schedule expiry: {e}",
            )

    def schedule_expiry_after(self, file: Nautilus.FileInfo, expire_after: int):
        try:
            schedule_file_expiry_after(file.get_location().get_path(), expire_after)
        except Exception as e:
            message_alert(
                heading="Expiry Scheduling Error",
                body=f"Failed to schedule expiry: {e}",
            )
