import tkinter as tk
import tkinter.filedialog as fd
from tkinter import ttk, messagebox
import shutil
import os
import threading


def select_source():
    path = fd.askdirectory()
    if path:
        entry_source.delete(0, "end")
        entry_source.insert(0, path)


def select_target():
    path = fd.askdirectory(initialdir=".")
    if path:
        entry_target.delete(0, "end")
        entry_target.insert(0, path)


def select_list():
    filetypes = (('Text files', '*.txt'), ('All files', '*.*'))
    path = fd.askopenfilename(
        title='Liste Seciniz', initialdir=".", filetypes=filetypes
    )
    if path:
        entry_list.delete(0, "end")
        entry_list.insert(0, path)


def validate_inputs():
    operation = radio_var.get()
    if not entry_source.get():
        messagebox.showwarning("Uyari", "Kaynak klasor seciniz!")
        return False
    if not entry_list.get() or entry_list.get() == "txt icinde bos satir olmayacak":
        messagebox.showwarning("Uyari", "Liste dosyasi seciniz!")
        return False
    if operation in (1, 3) and not entry_target.get():
        messagebox.showwarning("Uyari", "Hedef klasor seciniz!")
        return False
    if operation == 0:
        messagebox.showwarning("Uyari", "Bir islem seciniz!")
        return False
    return True


def run_operation():
    if not validate_inputs():
        return

    operation = radio_var.get()
    source_dir = entry_source.get()
    target_dir = entry_target.get()
    list_path = entry_list.get()

    # ── Listeyi oku, boş satırları filtrele ──
    try:
        with open(list_path, "r", encoding="utf-8") as f:
            file_list = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        messagebox.showerror("Hata", f"Dosya bulunamadi:\n{list_path}")
        return

    if not file_list:
        messagebox.showwarning("Uyari", "Liste bos!")
        return

    # ── Progress penceresi ──
    progress_win = tk.Toplevel(root)
    progress_win.title("Islem Devam Ediyor...")
    progress_win.geometry("350x120")
    progress_win.resizable(False, False)
    progress_win.grab_set()

    progress = ttk.Progressbar(
        progress_win, orient="horizontal", length=300, mode="determinate"
    )
    progress.pack(pady=15)

    status_label = tk.Label(progress_win, font="Arial 10 bold", text="% 0")
    status_label.pack()

    # ── Butonları devre dışı bırak ──
    btn_run.config(state="disabled")

    # ════════════════════════════════════════
    #  ASIL İŞLEM → AYRI THREAD'DE ÇALIŞIR
    # ════════════════════════════════════════
    def worker():
        total = len(file_list)
        errors = []
        last_pct = -1  # Gereksiz GUI güncellemelerini önle

        for idx, filename in enumerate(file_list, start=1):
            src = os.path.join(source_dir, filename)

            try:
                if operation == 1:      # COPY
                    shutil.copy2(src, target_dir)
                elif operation == 2:    # DELETE
                    os.remove(src)
                elif operation == 3:    # MOVE
                    shutil.move(src, target_dir)
            except FileNotFoundError:
                errors.append(f"BULUNAMADI: {filename}")
            except PermissionError:
                errors.append(f"ERISIM ENGELI: {filename}")
            except Exception as e:
                errors.append(f"{filename}: {e}")

            # ── Yüzde değiştiyse GUI güncelle (her dosyada değil!) ──
            pct = int(idx / total * 100)
            if pct != last_pct:
                last_pct = pct
                # thread-safe GUI güncelleme
                progress_win.after(0, update_progress, pct, idx, total)

        # İşlem bitti → ana thread'de kapat
        progress_win.after(0, finish, errors)

    def update_progress(pct, idx, total):
        """Progress bar ve label güncelle (ana thread'de çalışır)."""
        try:
            progress["value"] = pct
            status_label.config(text=f"% {pct}   ({idx} / {total})")
        except tk.TclError:
            pass  # pencere kapandıysa hata vermesin

    def finish(errors):
        """İşlem bitince pencereyi kapat, sonucu göster."""
        try:
            progress_win.destroy()
        except tk.TclError:
            pass

        btn_run.config(state="normal")

        op_names = {1: "KOPYALAMA", 2: "SILME", 3: "TASIMA"}
        op_name = op_names.get(operation, "ISLEM")

        if errors:
            msg = "\n".join(errors[:25])
            messagebox.showwarning(
                "SONUC",
                f"{op_name} tamamlandi.\n\n"
                f"Hatali dosya sayisi: {len(errors)}\n{msg}"
            )
        else:
            messagebox.showinfo("SONUC", f"{op_name} TAMAM!")

    # Thread başlat (GUI donmaz)
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()


# ═══════════════════════════════════════
#  ANA PENCERE
# ═══════════════════════════════════════
root = tk.Tk()
root.geometry("480x290")
root.title("File Copy / Move / Delete  v0.006")
root.resizable(False, False)

# Kaynak
tk.Label(root, text="Kaynak Klasor Seciniz").place(x=10, y=20)
entry_source = tk.Entry(root, font="Arial 8 bold")
entry_source.place(x=200, y=20, width=220, height=25)
tk.Button(root, fg="blue", text="...", command=select_source).place(x=430, y=18)

# Hedef
tk.Label(root, text="Hedef Klasor Seciniz").place(x=10, y=60)
entry_target = tk.Entry(root, font="Arial 8 bold")
entry_target.place(x=200, y=60, width=220, height=25)
tk.Button(root, fg="blue", text="...", command=select_target).place(x=430, y=58)

# Liste
tk.Label(root, text="Liste Seciniz").place(x=10, y=100)
entry_list = tk.Entry(root, font="Arial 8 bold")
entry_list.insert(0, "txt icinde bos satir olmayacak")
entry_list.place(x=200, y=100, width=220, height=25)
tk.Button(root, fg="blue", text="...", command=select_list).place(x=430, y=98)

# İşlem seçimi
radio_var = tk.IntVar(value=0)
tk.Radiobutton(root, text="Copy",  variable=radio_var, value=1).place(x=50,  y=150)
tk.Radiobutton(root, text="Move",  variable=radio_var, value=3).place(x=180, y=150)
tk.Radiobutton(root, text="Delete",variable=radio_var, value=2).place(x=310, y=150)

# Butonlar
btn_run = tk.Button(
    root, text="CALISTIR", font="Arial 14 bold", fg="green", command=run_operation
)
btn_run.place(x=20, y=200)

tk.Button(
    root, text="CIKIS", font="Arial 14 bold", fg="red", command=root.destroy
).place(x=380, y=200)

tk.Label(root, font="Arial 9 bold", text="PROGRAM BY").place(x=150, y=260)
tk.Label(root, font="Arial 9 bold", fg="blue", text="OSMAN ULUCA").place(x=240, y=260)

root.mainloop()
