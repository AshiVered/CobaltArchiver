import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import os
import re


# פונקציה לדחיסת קבצים לארכיון
def compress():
    files_to_compress = filedialog.askopenfilenames(title="בחר קבצים לדחיסה")
    if files_to_compress:
        archive_name = filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("Zip Files", "*.zip"), ("7z Files", "*.7z"), 
                      ("Tar Files", "*.tar"), ("Wim Files", "*.wim"), ("All files", "*.*")], title="בחר שם לארכיון")
        if archive_name:
            try:
                subprocess.run(["7z", "a", archive_name] + list(files_to_compress), check=True)
                messagebox.showinfo("הצלחה", f"הקבצים דחוסים בהצלחה לארכיון {archive_name}.")
            except subprocess.CalledProcessError as e:
                messagebox.showerror("שגיאה", f"שגיאה בדחיסת הקבצים: {e}")
    else:
        messagebox.showwarning("שגיאה", "לא נבחרו קבצים לדחיסה.")


# פונקציה לחילוץ קבצים מארכיון
def extract():
    archive_name = filedialog.askopenfilename(title="בחר את הארכיון לחילוץ",    filetypes=[
        ("Archive Files", "*.zip *.7z *.rar *.tar *.gz *.bz2 *.xz *.wim"),
        ("All files", "*.*")
    ]
)
    if archive_name:
        extract_dir = filedialog.askdirectory(title="בחר תיקיה לחילוץ הקבצים")
        if extract_dir:
            # בדיקה אם יש קבצים קיימים בתיקיה עם אותם שמות
            existing_files = os.listdir(extract_dir)
            process = subprocess.Popen(["7z", "l", archive_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            stdout = stdout.decode("utf-8", errors="ignore")
            files_to_extract = [line.split()[-1] for line in stdout.splitlines() if line]

            # קובעים אם יש קובץ קיים שצריך לטפל בו
            overlapping_files = [file for file in files_to_extract if file in existing_files]
            
            if overlapping_files:
                response = messagebox.askquestion(
                    "קבצים קיימים",
                    f"הקבצים הבאים כבר קיימים בתיקיה:\n\n" + "\n".join(overlapping_files) +
                    "\n\nהאם להמשיך ולדרוס את הקבצים הקיימים?",
                )
                if response == "yes":
                    try:
                        subprocess.run(["7z", "x", archive_name, f"-o{extract_dir}", "-y"], check=True)
                        messagebox.showinfo("הצלחה", f"הקבצים חולצו בהצלחה לתיקיה {extract_dir}.")
                    except subprocess.CalledProcessError as e:
                        messagebox.showerror("שגיאה", f"שגיאה בחילוץ הקבצים: {e}")
                else:
                    messagebox.showinfo("בוטל", "החילוץ בוטל.")
            else:
                try:
                    subprocess.run(["7z", "x", archive_name, f"-o{extract_dir}"], check=True)
                    messagebox.showinfo("הצלחה", f"הקבצים חולצו בהצלחה לתיקיה {extract_dir}.")
                except subprocess.CalledProcessError as e:
                    messagebox.showerror("שגיאה", f"שגיאה בחילוץ הקבצים: {e}")
    else:
        messagebox.showwarning("שגיאה", "לא נבחר ארכיון לחילוץ.")


# פונקציה להצגת תוכן הארכיון
def show_archive():
    archive_name = filedialog.askopenfilename(title="בחר את הארכיון לצפייה",     filetypes=[
        ("Archive Files", "*.zip *.7z *.rar *.tar *.gz *.bz2 *.xz *.wim"),
        ("All files", "*.*")
    ]
)
    if archive_name:
        try:
            # קריאת הפלט בצורה בינארית
            process = subprocess.Popen(
                ["7z", "l", archive_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()

            # המרת הפלט ל-UTF-8
            try:
                stdout = stdout.decode("utf-8")
            except UnicodeDecodeError:
                # טיפול במקרה של קידוד לא תקין
                stdout = stdout.decode("latin-1")  # ניסיון עם קידוד חלופי
                messagebox.showwarning("אזהרה", "הארכיון אינו בקידוד UTF-8, ייתכנו בעיות בהצגת נתונים.")

            if process.returncode != 0:
                raise Exception(f"לא ניתן להפעיל את הפקודה 7z: {stderr.decode('utf-8', errors='ignore')}")

            file_info = []
            file_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\d+)\s+(\d+|)\s+(.+)$")

            for line in stdout.splitlines():
                match = file_pattern.match(line)
                if match:
                    date_modified = match.group(1)
                    time_modified = match.group(2)
                    attr = match.group(3)
                    size = match.group(4)
                    compressed = match.group(5) or "N/A"
                    filename = match.group(6)

                    file_info.append((filename, size, compressed, date_modified, time_modified))

            if file_info:
                show_archive_window(file_info, archive_name)
            else:
                messagebox.showerror("שגיאה", "לא נמצאו קבצים בארכיון.")
        except Exception as e:
            messagebox.showerror("שגיאה לא צפויה", f"שגיאה: {e}")



# פונקציה להצגת תוכן הארכיון בחלון חדש עם לחצנים להסרה והוספה
# פונקציה להצגת תוכן הארכיון בחלון חדש
# פונקציה להצגת תוכן הארכיון בחלון חדש
def show_archive_window(file_info, archive_name):
    def add_file():
        files_to_add = filedialog.askopenfilenames(title="בחר קבצים להוספה לארכיון")
        if files_to_add:
            try:
                subprocess.run(["7z", "a", archive_name] + list(files_to_add), check=True)
                messagebox.showinfo("הצלחה", f"הקבצים נוספו בהצלחה לארכיון {archive_name}.")
                refresh_file_list()  # רענון הרשימה
            except subprocess.CalledProcessError as e:
                messagebox.showerror("שגיאה", f"שגיאה בהוספת קבצים לארכיון: {e}")

    def remove_file():
        selected_item = tree.focus()
        if not selected_item:
            messagebox.showwarning("שגיאה", "לא נבחר קובץ להסרה.")
            return

        filename = tree.item(selected_item)["values"][0]
        try:
            subprocess.run(["7z", "d", archive_name, filename], check=True)
            messagebox.showinfo("הצלחה", f"הקובץ {filename} הוסר בהצלחה מהארכיון.")
            refresh_file_list()  # רענון הרשימה
        except subprocess.CalledProcessError as e:
            messagebox.showerror("שגיאה", f"שגיאה בהסרת קובץ מהארכיון: {e}")

    def refresh_file_list():
        tree.delete(*tree.get_children())
        updated_info = get_archive_file_info(archive_name)
        for file in updated_info:
            # הוספת תנאי לדילוג על השורה "files"
            if file[0] != "files":
                tree.insert("", "end", values=file)

    def open_file(event):
        selected_item = tree.focus()
        if not selected_item:
            return

        filename = tree.item(selected_item)["values"][0]
        try:
            full_path = os.path.join(os.path.dirname(archive_name), filename)
            os.startfile(full_path)
        except Exception as e:
            messagebox.showerror("שגיאה", f"לא ניתן לפתוח את הקובץ: {e}")

    window = tk.Toplevel()
    window.title(f"תוכן הארכיון: {os.path.basename(archive_name)}")
    window.geometry("700x400")

    tree = ttk.Treeview(window, columns=("filename", "size", "compressed", "date_modified", "time_modified"), show="headings")
    tree.heading("filename", text="שם קובץ")
    tree.heading("size", text="גודל מקורי (bytes)")
    tree.heading("compressed", text="גודל דחוס (bytes)")
    tree.heading("date_modified", text="תאריך שינוי")
    tree.heading("time_modified", text="שעת שינוי")

    tree.column("filename", width=300)
    tree.column("size", width=100, anchor="center")
    tree.column("compressed", width=100, anchor="center")
    tree.column("date_modified", width=120, anchor="center")
    tree.column("time_modified", width=120, anchor="center")

    for file in file_info:
        # הוספת תנאי לדילוג על השורה "files"
        if file[0] != "files":
            tree.insert("", "end", values=file)

    tree.pack(fill="both", expand=True)
    tree.bind("<Double-1>", open_file)

    button_frame = tk.Frame(window)
    button_frame.pack(fill="x", pady=5)
    try:
        window.iconbitmap("icon.ico")  # החלף את 'path_to_icon.ico' בנתיב לקובץ ה-ICO שלך
    except Exception as e:
        print(f"שגיאה בטעינת סמל: {e}")

    tk.Button(button_frame, text="הוסף קובץ", command=add_file).pack(side="left", padx=5)
    tk.Button(button_frame, text="הסר קובץ", command=remove_file).pack(side="left", padx=5)

    window.mainloop()

# פונקציה לקבלת תוכן הארכיון המעודכן
def get_archive_file_info(archive_name):
    try:
        process = subprocess.Popen(["7z", "l", archive_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        stdout = stdout.decode("utf-8", errors="ignore")

        file_info = []
        file_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\d+)\s+(\d+|)\s+(.+)$")

        for line in stdout.splitlines():
            match = file_pattern.match(line)
            if match:
                date_modified = match.group(1)
                time_modified = match.group(2)
                attr = match.group(3)
                size = match.group(4)
                compressed = match.group(5) or "N/A"
                filename = match.group(6)
                file_info.append((filename, size, compressed, date_modified, time_modified))

        return file_info
    except Exception as e:
        messagebox.showerror("שגיאה", f"לא ניתן לקרוא את תוכן הארכיון: {e}")
        return []

def show_about():
    about_window = tk.Toplevel()
    about_window.title("אודות התוכנה")
    try:
        about_window.iconbitmap("icon.ico")  # החלף את 'path_to_icon.ico' בנתיב לקובץ ה-ICO שלך
    except Exception as e:
        print(f"שגיאה בטעינת סמל: {e}")
    # הגדרת מסגרת לתוכן
    content_frame = tk.Frame(about_window, padx=10, pady=10)
    content_frame.pack()

    # שורה ראשונה - כותרת
    tk.Label(
        content_frame,
        text="CobaltArchiver",
        font=("Arial", 14, "bold"),  # פונט מודגש וגדול יותר
        anchor="center"
    ).pack()

    # שורה שנייה - גרסא
    tk.Label(
        content_frame,
        text="גרסא 0.3",
        font=("Arial", 10),
        anchor="center"
    ).pack()

    # רווח
    tk.Label(content_frame, text="").pack()

    # שורות נוספות עם המידע
    tk.Label(
        content_frame,
        text="פותח על ידי אשי ורד",
        font=("Arial", 10),
        anchor="center"
    ).pack()

    tk.Label(
        content_frame,
        text="עבור ישיבת מדברה כעדן - מצפה רמון",
        font=("Arial", 10),
        anchor="center"
    ).pack()

    # מסגרת ללחצנים
    button_frame = tk.Frame(about_window, pady=10)
    button_frame.pack()

    # לחצן GitHub
    def open_github():
        import webbrowser
        webbrowser.open("https://github.com/ashivered/cobaltarchiver")

    tk.Button(
        button_frame,
        text="GitHub",
        command=open_github
    ).pack(side="left", padx=5)

    # לחצן Icons
    def open_icons():
        import webbrowser
        webbrowser.open("https://icons8.com")

    tk.Button(
        button_frame,
        text="Icons by icons8.com",
        command=open_icons
    ).pack(side="left", padx=5)

    # התאמת גודל החלון לתוכן
    about_window.update_idletasks()
    width = about_window.winfo_reqwidth()
    height = about_window.winfo_reqheight()
    about_window.geometry(f"{width}x{height}")



# יצירת הממשק הראשי
def main():
    root = tk.Tk()
    root.title("CobaltArchiver")
    root.geometry("300x200")
    try:
        root.iconbitmap("icon.ico")  # החלף את 'path_to_icon.ico' בנתיב לקובץ ה-ICO שלך
    except Exception as e:
        print(f"שגיאה בטעינת סמל: {e}")

    tk.Button(root, text="דחיסת קבצים", command=compress, width=20).pack(pady=10)
    tk.Button(root, text="חילוץ קבצים", command=extract, width=20).pack(pady=10)
    tk.Button(root, text="הצגת תוכן ארכיון", command=show_archive, width=20).pack(pady=10)
    tk.Button(root, text="אודות התוכנה", command=show_about, width=20).pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()
