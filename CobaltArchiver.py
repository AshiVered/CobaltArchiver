import wx
import subprocess
import os
import re
import webbrowser

class ArchiveViewerFrame(wx.Frame):
    """
    Frame for viewing archive content (Table View).
    Equivalent to the 'show_archive_window' function in the original code.
    """
    def __init__(self, parent, file_info, archive_name):
        super().__init__(parent, title=f"Archive Content: {os.path.basename(archive_name)}", size=(700, 400))
        self.archive_name = archive_name
        
        # Set Icon
        try:
            if os.path.exists("icon.ico"):
                self.SetIcon(wx.Icon("icon.ico"))
        except Exception as e:
            print(f"Error loading icon: {e}")

        # Main Layout
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # ListCtrl (Table) setup
        self.list_ctrl = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.list_ctrl.InsertColumn(0, "Filename", width=300)
        self.list_ctrl.InsertColumn(1, "Original Size (bytes)", width=120)
        self.list_ctrl.InsertColumn(2, "Compressed Size (bytes)", width=150)
        self.list_ctrl.InsertColumn(3, "Date Modified", width=120)
        self.list_ctrl.InsertColumn(4, "Time Modified", width=120)

        # Populate list
        self.populate_list(file_info)

        vbox.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 5)

        # Buttons
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        
        btn_add = wx.Button(panel, label="Add File")
        btn_add.Bind(wx.EVT_BUTTON, self.on_add_file)
        hbox.Add(btn_add, 0, wx.RIGHT, 5)

        btn_remove = wx.Button(panel, label="Remove File")
        btn_remove.Bind(wx.EVT_BUTTON, self.on_remove_file)
        hbox.Add(btn_remove, 0, wx.RIGHT, 5)

        vbox.Add(hbox, 0, wx.ALIGN_LEFT | wx.ALL, 5)

        panel.SetSizer(vbox)

        # Bind Double Click
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_open_file)
        
        self.Centre()
        self.Show()

    def populate_list(self, file_info):
        self.list_ctrl.DeleteAllItems()
        for item in file_info:
            # Skip the "files" summary line usually at the end of 7z output if caught
            if item[0] != "files": 
                index = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), item[0])
                self.list_ctrl.SetItem(index, 1, item[1])
                self.list_ctrl.SetItem(index, 2, item[2])
                self.list_ctrl.SetItem(index, 3, item[3])
                self.list_ctrl.SetItem(index, 4, item[4])

    def get_archive_file_info(self):
        """Helper to re-fetch archive info after modification"""
        try:
            process = subprocess.Popen(["7z", "l", self.archive_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            stdout = stdout.decode("utf-8", errors="ignore")

            file_info = []
            file_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\d+)\s+(\d+|)\s+(.+)$")

            for line in stdout.splitlines():
                match = file_pattern.match(line)
                if match:
                    date_modified = match.group(1)
                    time_modified = match.group(2)
                    # attr = match.group(3) # Not used in display
                    size = match.group(4)
                    compressed = match.group(5) or "N/A"
                    filename = match.group(6)
                    file_info.append((filename, size, compressed, date_modified, time_modified))

            return file_info
        except Exception as e:
            wx.MessageBox(f"Cannot read archive content: {e}", "Error", wx.OK | wx.ICON_ERROR)
            return []

    def refresh_file_list(self):
        updated_info = self.get_archive_file_info()
        self.populate_list(updated_info)

    def on_add_file(self, event):
        with wx.FileDialog(self, "Select files to add to archive", style=wx.FD_OPEN | wx.FD_MULTIPLE) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            files_to_add = fileDialog.GetPaths()
            
            if files_to_add:
                try:
                    subprocess.run(["7z", "a", self.archive_name] + files_to_add, check=True)
                    wx.MessageBox(f"Files successfully added to archive {self.archive_name}.", "Success", wx.OK | wx.ICON_INFORMATION)
                    self.refresh_file_list()
                except subprocess.CalledProcessError as e:
                    wx.MessageBox(f"Error adding files to archive: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def on_remove_file(self, event):
        selected_index = self.list_ctrl.GetFirstSelected()
        if selected_index == -1:
            wx.MessageBox("No file selected for removal.", "Error", wx.OK | wx.ICON_WARNING)
            return

        filename = self.list_ctrl.GetItemText(selected_index, 0) # Column 0 is filename
        try:
            subprocess.run(["7z", "d", self.archive_name, filename], check=True)
            wx.MessageBox(f"File {filename} successfully removed from archive.", "Success", wx.OK | wx.ICON_INFORMATION)
            self.refresh_file_list()
        except subprocess.CalledProcessError as e:
            wx.MessageBox(f"Error removing file from archive: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def on_open_file(self, event):
        selected_index = event.GetIndex()
        filename = self.list_ctrl.GetItemText(selected_index, 0)
        try:
            # Logic from original code: tries to open file at path relative to archive location
            full_path = os.path.join(os.path.dirname(self.archive_name), filename)
            os.startfile(full_path)
        except Exception as e:
            wx.MessageBox(f"Cannot open file: {e}", "Error", wx.OK | wx.ICON_ERROR)


class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="CobaltArchiver", size=(300, 250))
        
        # Set Icon
        try:
            if os.path.exists("icon.ico"):
                self.SetIcon(wx.Icon("icon.ico"))
        except Exception as e:
            print(f"Error loading icon: {e}")

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Buttons
        btn_compress = wx.Button(panel, label="Compress Files")
        btn_compress.Bind(wx.EVT_BUTTON, self.on_compress)
        vbox.Add(btn_compress, 0, wx.ALL | wx.EXPAND, 10)

        btn_extract = wx.Button(panel, label="Extract Files")
        btn_extract.Bind(wx.EVT_BUTTON, self.on_extract)
        vbox.Add(btn_extract, 0, wx.ALL | wx.EXPAND, 10)

        btn_show = wx.Button(panel, label="Show Archive Content")
        btn_show.Bind(wx.EVT_BUTTON, self.on_show_archive)
        vbox.Add(btn_show, 0, wx.ALL | wx.EXPAND, 10)

        btn_about = wx.Button(panel, label="About")
        btn_about.Bind(wx.EVT_BUTTON, self.on_about)
        vbox.Add(btn_about, 0, wx.ALL | wx.EXPAND, 10)

        panel.SetSizer(vbox)
        self.Centre()

    def on_compress(self, event):
        with wx.FileDialog(self, "Select files to compress", style=wx.FD_OPEN | wx.FD_MULTIPLE) as openFileDialog:
            if openFileDialog.ShowModal() == wx.ID_CANCEL:
                wx.MessageBox("No files selected for compression.", "Error", wx.OK | wx.ICON_WARNING)
                return
            
            files_to_compress = openFileDialog.GetPaths()
            
            wildcard = "Zip Files (*.zip)|*.zip|7z Files (*.7z)|*.7z|Tar Files (*.tar)|*.tar|Wim Files (*.wim)|*.wim|All files (*.*)|*.*"
            with wx.FileDialog(self, "Save archive as", wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as saveFileDialog:
                # Set default extension based on choice if possible, but FD_SAVE handles most
                if saveFileDialog.ShowModal() == wx.ID_CANCEL:
                    return
                
                archive_name = saveFileDialog.GetPath()
                
                # Ensure extension is present if user didn't type it (simple check)
                if not os.path.splitext(archive_name)[1]:
                    archive_name += ".zip"

                try:
                    subprocess.run(["7z", "a", archive_name] + files_to_compress, check=True)
                    wx.MessageBox(f"Files successfully compressed to {archive_name}.", "Success", wx.OK | wx.ICON_INFORMATION)
                except subprocess.CalledProcessError as e:
                    wx.MessageBox(f"Error compressing files: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def on_extract(self, event):
        wildcard = "Archive Files (*.zip;*.7z;*.rar;*.tar;*.gz;*.bz2;*.xz;*.wim)|*.zip;*.7z;*.rar;*.tar;*.gz;*.bz2;*.xz;*.wim|All files (*.*)|*.*"
        with wx.FileDialog(self, "Select archive to extract", wildcard=wildcard, style=wx.FD_OPEN) as openFileDialog:
            if openFileDialog.ShowModal() == wx.ID_CANCEL:
                wx.MessageBox("No archive selected for extraction.", "Error", wx.OK | wx.ICON_WARNING)
                return
            
            archive_name = openFileDialog.GetPath()
            
            with wx.DirDialog(self, "Select destination folder", style=wx.DD_DEFAULT_STYLE) as dirDialog:
                if dirDialog.ShowModal() == wx.ID_CANCEL:
                    return
                
                extract_dir = dirDialog.GetPath()
                
                # Check for existing files
                existing_files = os.listdir(extract_dir)
                try:
                    process = subprocess.Popen(["7z", "l", archive_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    stdout, stderr = process.communicate()
                    stdout = stdout.decode("utf-8", errors="ignore")
                    
                    # Logic to parse filenames from list output
                    files_to_extract = [line.split()[-1] for line in stdout.splitlines() if line]

                    overlapping_files = [f for f in files_to_extract if f in existing_files]
                    
                    should_extract = True
                    if overlapping_files:
                        msg = "The following files already exist in the folder:\n\n" + "\n".join(overlapping_files) + \
                              "\n\nDo you want to continue and overwrite existing files?"
                        dlg = wx.MessageDialog(self, msg, "Existing Files", wx.YES_NO | wx.ICON_QUESTION)
                        if dlg.ShowModal() != wx.ID_YES:
                            should_extract = False
                            wx.MessageBox("Extraction cancelled.", "Cancelled", wx.OK | wx.ICON_INFORMATION)
                        dlg.Destroy()
                    
                    if should_extract:
                        flags = ["7z", "x", archive_name, f"-o{extract_dir}"]
                        if overlapping_files:
                            flags.append("-y") # Yes to all
                        
                        subprocess.run(flags, check=True)
                        wx.MessageBox(f"Files extracted successfully to {extract_dir}.", "Success", wx.OK | wx.ICON_INFORMATION)
                        
                except subprocess.CalledProcessError as e:
                    wx.MessageBox(f"Error extracting files: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def on_show_archive(self, event):
        wildcard = "Archive Files (*.zip;*.7z;*.rar;*.tar;*.gz;*.bz2;*.xz;*.wim)|*.zip;*.7z;*.rar;*.tar;*.gz;*.bz2;*.xz;*.wim|All files (*.*)|*.*"
        with wx.FileDialog(self, "Select archive to view", wildcard=wildcard, style=wx.FD_OPEN) as openFileDialog:
            if openFileDialog.ShowModal() == wx.ID_CANCEL:
                return
            
            archive_name = openFileDialog.GetPath()
            
            try:
                process = subprocess.Popen(
                    ["7z", "l", archive_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout, stderr = process.communicate()

                # Decode logic from original
                try:
                    stdout_decoded = stdout.decode("utf-8")
                except UnicodeDecodeError:
                    stdout_decoded = stdout.decode("latin-1")
                    wx.MessageBox("The archive is not UTF-8 encoded, data display issues may occur.", "Warning", wx.OK | wx.ICON_WARNING)

                if process.returncode != 0:
                    raise Exception(f"Could not run 7z command: {stderr.decode('utf-8', errors='ignore')}")

                file_info = []
                file_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\d+)\s+(\d+|)\s+(.+)$")

                for line in stdout_decoded.splitlines():
                    match = file_pattern.match(line)
                    if match:
                        date_modified = match.group(1)
                        time_modified = match.group(2)
                        # attr = match.group(3)
                        size = match.group(4)
                        compressed = match.group(5) or "N/A"
                        filename = match.group(6)

                        file_info.append((filename, size, compressed, date_modified, time_modified))

                if file_info:
                    ArchiveViewerFrame(self, file_info, archive_name)
                else:
                    wx.MessageBox("No files found in archive.", "Error", wx.OK | wx.ICON_ERROR)

            except Exception as e:
                wx.MessageBox(f"Unexpected error: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def on_about(self, event):
        about_dlg = wx.Dialog(self, title="About", size=(350, 250))
        
        # Set Icon for dialog
        try:
            if os.path.exists("icon.ico"):
                about_dlg.SetIcon(wx.Icon("icon.ico"))
        except Exception:
            pass

        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Title
        lbl_title = wx.StaticText(about_dlg, label="CobaltArchiver")
        font_title = lbl_title.GetFont()
        font_title.SetPointSize(14)
        font_title.SetWeight(wx.FONTWEIGHT_BOLD)
        lbl_title.SetFont(font_title)
        vbox.Add(lbl_title, 0, wx.ALIGN_CENTER | wx.TOP, 15)

        # Version
        lbl_ver = wx.StaticText(about_dlg, label="Version 0.4")
        vbox.Add(lbl_ver, 0, wx.ALIGN_CENTER | wx.TOP, 5)

        vbox.Add((0, 15)) # Spacer

        # Credits
        lbl_dev = wx.StaticText(about_dlg, label="Developed by Ashi Vered")
        vbox.Add(lbl_dev, 0, wx.ALIGN_CENTER | wx.TOP, 5)
        # Buttons Box
        hbox_btns = wx.BoxSizer(wx.HORIZONTAL)
        
        btn_github = wx.Button(about_dlg, label="GitHub")
        btn_github.Bind(wx.EVT_BUTTON, lambda e: webbrowser.open("https://github.com/ashivered/cobaltarchiver"))
        hbox_btns.Add(btn_github, 0, wx.ALL, 5)

        btn_icons = wx.Button(about_dlg, label="Icons by icons8.com")
        btn_icons.Bind(wx.EVT_BUTTON, lambda e: webbrowser.open("https://icons8.com"))
        hbox_btns.Add(btn_icons, 0, wx.ALL, 5)

        vbox.Add(hbox_btns, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 15)

        about_dlg.SetSizer(vbox)
        about_dlg.Centre()
        about_dlg.ShowModal()
        about_dlg.Destroy()

if __name__ == "__main__":
    app = wx.App(False)
    frame = MainFrame()
    frame.Show()
    app.MainLoop()