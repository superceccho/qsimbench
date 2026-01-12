import customtkinter as ctk
from customtkinter import filedialog
from PIL import Image

from dotenv import dotenv_values, set_key
import os
import json
from pathlib import Path
from datetime import datetime
import importlib
import sys
import threading

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("theme.json")

def display_error(mex):
    response_text.configure(state="normal")
    response_text.insert(ctk.END, "[ERR]" + mex, "red")
    response_text.configure(state="disabled")
    response_text.see(ctk.END)

def display_message(mex):
    response_text.configure(state="normal")
    response_text.insert(ctk.END, mex, "white")
    response_text.configure(state="disabled")
    response_text.see(ctk.END)

def clear_text():
    response_text.configure(state="normal")
    response_text.delete(0.0, ctk.END)
    response_text.configure(state="disabled")

class ScrollableOption(ctk.CTkToplevel):
    def __init__(self, master, entry):
        super().__init__(master)

        self.overrideredirect(True)

        x = entry.winfo_rootx()
        y = entry.winfo_rooty() + entry.winfo_height()

        self.geometry(f"+{x}+{y}")

        self.frame = ctk.CTkScrollableFrame(self, width=230)
        self.frame.pack()

        self.entry = entry

        self.buttons = []
        
    def select(self, text):
        self.entry.configure(state="normal")
        self.entry.delete(0, ctk.END)
        self.entry.insert(0, text)
        self.entry.configure(state="disabled")

        self.destroy()

    def set_values(self, values):
        for button in self.buttons:
            button.destroy()
        
        for value in values:
            button = ctk.CTkButton(self.frame, text=value, border_width=0, corner_radius=0, command=lambda v=value: self.select(v))
            button.pack(fill=ctk.X)
            self.buttons.append(button)

class DropDown(ctk.CTkEntry):
    def __init__(self, master, width = 140, height = 28, corner_radius = None, border_width = None, bg_color = "transparent", fg_color = None, border_color = None, text_color = None, font = None, state = ctk.NORMAL, command = None, **kwargs):
        super().__init__(master, width, height, corner_radius, border_width, bg_color, fg_color, border_color, text_color, None, None, None, font, ctk.DISABLED, **kwargs)

        self.bind("<Button-1>", lambda event: self.open_dropdown(master))

        self.values=[]
        self.buttons=[]
        self.frame = None

        self.reset()

        self.set_state(state)

        self.command = command

    def open_dropdown(self, master):
        if self.frame:
            self.frame.destroy()
            self.frame = None
            return
        
        if self.state == "disabled":
            return

        self.frame = ctk.CTkToplevel(master)
        self.frame.overrideredirect(True)

        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()

        self.frame.geometry(f"+{x}+{y}")

        options = ctk.CTkScrollableFrame(self.frame, width=self.winfo_width()-20)
        options.pack()

        def selection(value):
            self.configure(state="normal")
            self.delete(0, ctk.END)
            self.insert(0, value)
            self.configure(state="disabled")

            self.frame.destroy()
            self.frame = None

            if self.command:
                self.command()

        for value in self.values:
            button = ctk.CTkButton(options, text=value, border_width=0, corner_radius=0, command=lambda v=value: selection(v))
            button.pack(fill=ctk.X)
            self.buttons.append(button)

    def get_value(self):
        return self.get() if self.get() != "#click to select" else None
    
    def set_values(self, values):
        self.values = values

    def reset(self):
        self.configure(state="normal")
        self.delete(0, ctk.END)
        self.insert(0, "#click to select")
        self.configure(state="disabled")

    def set_state(self, state):
        if state not in ["normal", "disabled"]:
            raise RuntimeError("State must be 'normal' or 'disabled'")
        
        if self.frame:
            self.frame.destroy()
            self.frame = None

        if state == "disabled":
            self.configure(text_color="#696969")
            self.reset()
        else:
            self.configure(text_color="white")

        self.state = state

env_path = ".env"

def open_welcome():
    welcome_window = ctk.CTk()
    welcome_window.update_idletasks()

    screen_w = welcome_window.winfo_screenwidth()
    screen_h = welcome_window.winfo_screenheight()

    WELCOME_WIDTH = 700
    WELCOME_HEIGHT = 500
    welcome_window.geometry(f"{WELCOME_WIDTH}x{WELCOME_HEIGHT}+{screen_w//2 - WELCOME_WIDTH//2}+{screen_h//2 - WELCOME_HEIGHT//2}")
    welcome_window.title("QSimBench")

    welcome_window.rowconfigure(0, weight=1)
    welcome_window.rowconfigure(1, weight=2)
    welcome_window.rowconfigure(2, weight=2)
    welcome_window.rowconfigure(3, weight=1)
    welcome_window.rowconfigure(4, weight=1)

    welcome_window.columnconfigure(0, weight=1)
    welcome_window.columnconfigure(1, weight=1)

    title_label = ctk.CTkLabel(welcome_window, text="Welcome to QSimBench", font=("", 50, "bold"))
    title_label.grid(row=0, column=0, columnspan=2)

    dataset_label = ctk.CTkLabel(welcome_window, text="Dataset's URL:")
    dataset_label.grid(row=1, column=0)

    dataset_entry = ctk.CTkEntry(welcome_window, width=300)
    dataset_entry.grid(row=1, column=1)

    token_label = ctk.CTkLabel(welcome_window, text="GitHub token\n(optional):")
    token_label.grid(row=2, column=0)

    token_entry = ctk.CTkEntry(welcome_window, width=300)
    token_entry.grid(row=2, column=1)

    def save_func():
        if not dataset_entry.get():
            response_text.configure(state="normal")
            response_text.delete(0.0, ctk.END)
            response_text.insert(ctk.END, "Please insert dataset's URL")
            response_text.configure(state="disabled")
            return
        
        if not dataset_entry.get().startswith(("http://", "https://")):
            response_text.configure(state="normal")
            response_text.delete(0.0, ctk.END)
            response_text.insert(ctk.END, "Dataset's URL must start with 'http://' or 'https://'")
            response_text.configure(state="disabled")
            return
        
        with open(env_path, "w") as file:
            file.write(f"QSIMBENCH_DATASET={dataset_entry.get()}\n" \
                       f"GITHUB_TOKEN={token_entry.get()}\n" \
                        f"QSIMBENCH_CACHE_TIMEOUT={60 * 60 * 24 * 30}\n" \
                        "OUTPUT_DIR=output")
            
        welcome_window.destroy()

    save_button = ctk.CTkButton(welcome_window, text="Let's start!", command=save_func)
    save_button.grid(row=3, column=0, columnspan=2)

    response_text = ctk.CTkTextbox(welcome_window, state="disabled", wrap="word", height=60, width=300, text_color="red")
    response_text.grid(row=4, column=0, columnspan=2)

    welcome_window.mainloop()

if not os.path.exists(env_path):
    open_welcome()

if not os.path.exists(env_path):
    sys.exit(0)

config = dotenv_values(env_path)

WIDTH = 1000
HEIGHT = 600

root = ctk.CTk()
root.update_idletasks()

screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()

root.geometry(f"{WIDTH}x{HEIGHT}+{screen_w//2 - WIDTH//2}+{screen_h//2 - HEIGHT//2}")
root.title("QSimBench")

root.rowconfigure(0, weight=1)
root.rowconfigure(1, weight=2)
root.rowconfigure(2, weight=2)
root.rowconfigure(3, weight=1)

root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=1)
root.columnconfigure(2, weight=3)

title_frame = ctk.CTkFrame(root)
title_frame.grid(row=0, column=0, columnspan=3, sticky="ew")

title_frame.columnconfigure(0, weight=1)
title_frame.columnconfigure(1, weight=2)
title_frame.columnconfigure(2, weight=1)

title_label = ctk.CTkLabel(title_frame, text="QSimBench", font=("DejaVu Sans", 60, "bold"))
title_label.grid(row=0, column=1)

logo_img = ctk.CTkImage(light_image=Image.open("assets/atom.png"), dark_image=Image.open("assets/atom_dark.png"), size=(100,100))
logo_label = ctk.CTkLabel(title_frame, image=logo_img, compound="none")
logo_label.grid(row=0, column=0)

def open_settings():
    SETTINGS_WIDTH = 500
    SETTINGS_HEIGHT = 300

    settings_window = ctk.CTkToplevel(root)
    settings_window.title("Settings")
    settings_window.geometry(f"{SETTINGS_WIDTH}x{SETTINGS_HEIGHT}+{screen_w//2 - SETTINGS_WIDTH//2}+{screen_h//2 - SETTINGS_HEIGHT//2}")
    settings_window.transient(root)
    settings_window.update_idletasks()
    settings_window.grab_set()
    settings_window.focus_set()

    settings_window.rowconfigure(0, weight=1)
    settings_window.rowconfigure(1, weight=1)
    settings_window.rowconfigure(2, weight=1)
    settings_window.rowconfigure(3, weight=1)
    settings_window.rowconfigure(4, weight=1)

    settings_window.columnconfigure(0, weight=1)
    settings_window.columnconfigure(1, weight=1)

    dataset_label = ctk.CTkLabel(settings_window, text="Dataset's URL:")
    dataset_label.grid(row=0, column=0)

    dataset_entry = ctk.CTkEntry(settings_window, width=300)
    dataset_entry.insert(0, config["QSIMBENCH_DATASET"])
    dataset_entry.grid(row=0, column=1)
    dataset_entry.focus_set()

    token_label = ctk.CTkLabel(settings_window, text="GitHub token:")
    token_label.grid(row=1, column=0)

    token_entry = ctk.CTkEntry(settings_window, width=300)
    token_entry.insert(0, config["GITHUB_TOKEN"])
    token_entry.grid(row=1, column=1)

    cache_label = ctk.CTkLabel(settings_window, text="Cache timeout:")
    cache_label.grid(row=2, column=0)

    cache_entry = ctk.CTkEntry(settings_window, width=300)
    cache_entry.insert(0, config["QSIMBENCH_CACHE_TIMEOUT"])
    cache_entry.grid(row=2, column=1)

    output_label = ctk.CTkLabel(settings_window, text="Output folder:")
    output_label.grid(row=3, column=0)

    output_var = ctk.StringVar(value=config["OUTPUT_DIR"])
    output_img = ctk.CTkImage(dark_image=Image.open("assets/folder_dark.png"), size=(30,30))
    output_button = ctk.CTkButton(settings_window, text="Choose", command=lambda: output_var.set(filedialog.askdirectory(initialdir=output_var.get())), image=output_img)
    output_button.grid(row=3, column=1)

    def save_func():
        clear_text()

        if not dataset_entry.get():
            display_error("Enter dataset's URL")
            return
        
        if not dataset_entry.get().startswith(("http://", "https://")):
            display_error("Dataset URL must start with 'http://' or 'https://'")
            return
        
        if not cache_entry.get().isdigit():
            display_error("Cache timer must be a positive integer")
            return
        
        set_key(env_path, "QSIMBENCH_DATASET", dataset_entry.get())
        set_key(env_path, "GITHUB_TOKEN", token_entry.get())
        set_key(env_path, "QSIMBENCH_CACHE_TIMEOUT", cache_entry.get())
        set_key(env_path, "OUTPUT_DIR", os.path.relpath(output_var.get()))

        global config

        if dataset_entry.get() != config["QSIMBENCH_DATASET"] or token_entry.get() != config["GITHUB_TOKEN"] or cache_entry.get() != config["QSIMBENCH_CACHE_TIMEOUT"]:
            if reload():
                display_message("Changes saved")
        else:
            display_message("Changes saved")

        config = dotenv_values(env_path)

        update_versions()

    save_img = ctk.CTkImage(dark_image=Image.open("assets/save2_dark.png"), size=(30,30))
    save_button = ctk.CTkButton(settings_window, text="Save", command=save_func, image=save_img, width=110)
    save_button.grid(row=4, column=1)

    def reload():
        global versions

        try:
            if "qsimbench" in sys.modules:
                qsb = sys.modules["qsimbench"]
                importlib.reload(qsb)
            else:
                import qsimbench as qsb
                
            globals()["qsb"] = qsb
            
            versions = qsb.get_versions()

            return True
        except Exception as e:
            display_error(f"{e}")
            versions = []
            
            return False

    def refresh():
        clear_text()
        if reload():
            display_message("Refreshed")
        
        update_versions()

    refresh_img = ctk.CTkImage(dark_image=Image.open("assets/reload_dark.png"), size=(30,30))
    refresh_button = ctk.CTkButton(settings_window, text="", image=refresh_img, command=refresh, width=40)
    refresh_button.grid(row=4, column=0)

    settings_window.mainloop()

settings_img = ctk.CTkImage(light_image=Image.open("assets/settings.png"), dark_image=Image.open("assets/settings_dark.png"), size=(30,30))
settings_button = ctk.CTkButton(title_frame, command=open_settings, image=settings_img, text="Settings")
settings_button.grid(row=0, column=2)

versions_super_frame = ctk.CTkFrame(root, fg_color="#3B3B3B")
versions_super_frame.grid(row=1, column=0, columnspan=2, ipadx=10, sticky="news", padx=10, pady=10)

versions_super_frame.rowconfigure(0, weight=1)
versions_super_frame.rowconfigure(1, weight=1)

versions_super_frame.columnconfigure(0, weight=1)
versions_super_frame.columnconfigure(1, weight=1)

versions_frame = ctk.CTkScrollableFrame(versions_super_frame, label_text="Versions\n(right click for version's info)", fg_color="#3B3B3B", corner_radius=5)
versions_frame.grid(row=0, column=0, columnspan=2, sticky="ew")

versions_buttons = []

def open_version(event, version_name):
    VERSION_WIDTH = 600
    VERSION_HEIGHT = 530

    version_window = ctk.CTkToplevel(root)
    version_window.title(version_name)
    version_window.geometry(f"{VERSION_WIDTH}x{VERSION_HEIGHT}+{screen_w//2 - VERSION_WIDTH//2}+{screen_h//2 - VERSION_HEIGHT//2 - 35}")
    version_window.transient(root)
    version_window.update_idletasks()
    version_window.grab_set()
    version_window.focus_set()

    version_window.rowconfigure(0, weight=1)
    version_window.rowconfigure(1, weight=1)
    version_window.rowconfigure(2, weight=1)
    version_window.rowconfigure(3, weight=1)
    version_window.rowconfigure(4, weight=1)

    version_window.columnconfigure(0, weight=1)
    version_window.columnconfigure(1, weight=1)
    version_window.columnconfigure(2, weight=1)

    name_label = ctk.CTkLabel(version_window, text=f"Version name: {version_name}", font=("DejaVu Sans", 30, "bold"))
    name_label.grid(row=0, column=0, columnspan=3)

    metadata_label = ctk.CTkLabel(version_window, text="Version metadata:")
    metadata_label.grid(row=1, column=0)

    version_text = ctk.CTkTextbox(version_window, height=350, width=280, wrap="none", font=("", 15))
    version_text.grid(row=2, column=0, padx=5)

    download_img = ctk.CTkImage(dark_image=Image.open("assets/download_dark.png"), size=(30, 30))

    def download_version_metadata():
        Path(f"{config['OUTPUT_DIR']}/{version_name}").mkdir(parents=True, exist_ok=True)

        path = f"{config['OUTPUT_DIR']}/{version_name}/metadata.json"
        with open(path, "w") as file:
            json.dump(metadata, file, indent=2)
        
        clear_text()
        display_message(f"Version metadata saved to {path}")

    metadata_button = ctk.CTkButton(version_window, text="Download version metadata", command=download_version_metadata, image=download_img)
    metadata_button.configure(state="disabled")
    metadata_button.grid(row=3, column=0)

    def open_comb_metadata():
        alg = alg_entry.get_value()
        size = size_entry.get_value()
        back = back_entry.get_value()

        if not alg or alg == "ALL":
            clear_text()
            display_error("Choose ONE algorithm")
            return
        
        if not size or size == "ALL":
            clear_text()
            display_error("Choose ONE size")
            return
        
        if not back or back == "ALL":
            clear_text()
            display_error("Choose ONE backend")
            return
        
        comb_name = f"{alg}_{size}_{back}"

        comb_window = ctk.CTkToplevel(version_window)
        comb_window.geometry(f"400x500+{screen_w//2 - 200}+{screen_h//2 - 250 - 20}")
        comb_window.title(comb_name)
        comb_window.transient(version_window)
        comb_window.update_idletasks()
        comb_window.grab_set()
        comb_window.focus_set()

        comb_label = ctk.CTkLabel(comb_window, text=f"{comb_name}\nrun metadata:", font=("", 18, "bold"))
        comb_label.pack(pady=10)

        comb_text = ctk.CTkTextbox(comb_window, width=300, height=375, font=("", 15), wrap="none")
        comb_text.pack(pady=10)

        metadata = {}
        
        download_comb = ctk.CTkButton(comb_window, text="Download", command=lambda: download_comb_metadata(comb_name, metadata), image=download_img)
        download_comb.configure(state="disabled")
        download_comb.pack(pady=10)

        def init_func():
            comb_text.insert(0.0, "Loading...")
            comb_text.configure(state="disabled")

            nonlocal metadata

            try:
                metadata = qsb.get_metadata(alg, size, back, version_name)
            except Exception as e:
                comb_text.configure(state="normal")
                comb_text.delete(0.0, ctk.END)
                comb_text.configure(text_color="red")
                comb_text.configure(font=("", 18))
                comb_text.configure(wrap="word")
                comb_text.insert(ctk.END, f"[ERR] {e}")
                comb_text.configure(state="disabled")
                return
        
            metadata_json = json.dumps(metadata, indent=2)
            comb_text.configure(state="normal")
            comb_text.delete(0.0, ctk.END)
            for line in metadata_json.splitlines():
                comb_text.insert(ctk.END, line)
                comb_text.insert(ctk.END, "\n")
            comb_text.configure(state="disabled")

            download_comb.configure(state="normal")

        init_thread = threading.Thread(target=init_func)
        init_thread.start()

        comb_window.mainloop()

    combination_frame = ctk.CTkFrame(version_window, fg_color="#3B3B3B")
    combination_frame.grid(row=2, column=1, columnspan=2, padx=5, pady=5)

    combination_frame.rowconfigure(0, weight=1)
    combination_frame.rowconfigure(1, weight=1)
    combination_frame.rowconfigure(2, weight=1)
    combination_frame.rowconfigure(3, weight=1)

    comb_label = ctk.CTkLabel(combination_frame, text="Runs metadata:", corner_radius=5)
    comb_label.grid(row=0, column=0, columnspan=2, pady=5)

    index = qsb.get_index(version=version_name)
    algs = ["ALL"]
    sizes = []
    backs = ["ALL"]

    for alg in index:
        if alg not in algs:
            algs.append(alg)
        for size in index[alg]:
            if size not in sizes:
                sizes.append(size)
            for back in index[alg][size]:
                if back not in backs:
                    backs.append(back)

    sizes.sort() 
    sizes = list(map(str, sizes))
    sizes.insert(0, "ALL")

    alg_entry = DropDown(combination_frame, width=250, border_width=0)
    alg_entry.set_values(algs)
    alg_entry.grid(row=1, column=0, padx=5, pady=15)

    size_entry = DropDown(combination_frame, width=250, border_width=0)
    size_entry.set_values(sizes)
    size_entry.grid(row=2, column=0, padx=5, pady=15)

    back_entry = DropDown(combination_frame, width=250, border_width=0)
    back_entry.set_values(backs)
    back_entry.grid(row=3, column=0, padx=5, pady=15)

    def download_comb_metadata(comb_name, metadata):
        Path(f"{config['OUTPUT_DIR']}/{version_name}").mkdir(parents=True, exist_ok=True)

        path=f"{config['OUTPUT_DIR']}/{version_name}/{comb_name}_metadata.json"
        with open(path, "w") as file:
            json.dump(metadata, file, indent=2)

        clear_text()
        display_message(f"Run metadata saved to {path}")

    open_metadata_button = ctk.CTkButton(version_window, text="Show run\nmetadata", command=open_comb_metadata)
    open_metadata_button.grid(row=3, column=1, padx=5, pady=5)

    def download_all_comb_metadata():
        alg_choice = alg_entry.get_value()
        size_choice = size_entry.get_value()
        back_choice = back_entry.get_value()

        if not alg_choice or not size_choice or not back_choice:
            clear_text()
            display_error("Select every parameter")
            return
        
        download_runs_metadata_button.configure(state="disabled")
        
        selected_algs = [alg for alg in algs if alg != "ALL"] if alg_choice == "ALL" else [alg_choice]
        selected_sizes = [size for size in sizes if size != "ALL"] if size_choice == "ALL" else [size_choice]
        selected_backs = [back for back in backs if back != "ALL"] if back_choice == "ALL" else [back_choice]

        comb_count = len(selected_algs) * len(selected_sizes) * len(selected_backs)
        bar_step = 1 / comb_count

        progress_bar = ctk.CTkProgressBar(version_window, width=300, height=15)
        progress_bar.set(0)
        progress_bar.grid(row=4, column=1, columnspan=2)

        def thread_func():
            for alg in selected_algs:
                for size in selected_sizes:
                    for back in selected_backs:
                        try:
                            metadata = qsb.get_metadata(alg, size, back, version_name)
                            download_comb_metadata(f"{alg}_{size}_{back}", metadata)
                        except Exception as e:
                            clear_text()
                            display_error(str(e))

                        progress_bar.set(progress_bar.get() + bar_step)
            
            download_runs_metadata_button.configure(state="normal")
            progress_bar.destroy()

            clear_text()
            display_message(f"All metadata downloaded to: {config['OUTPUT_DIR']}/{version_name}")

        thread = threading.Thread(target=thread_func)
        thread.start()

    download_runs_metadata_button = ctk.CTkButton(version_window, text="Download runs\nmetadata", command=download_all_comb_metadata)
    download_runs_metadata_button.grid(row=3, column=2)

    metadata = {}

    def init_func():
        version_text.insert(0.0, "Loading...")
        version_text.configure(state="disabled")
        nonlocal metadata
        try:
            metadata = qsb.get_version_metadata(version_name)
        except Exception as e:
            version_text.configure(state="normal")
            version_text.delete(0.0, ctk.END)
            version_text.configure(text_color="red")
            version_text.configure(wrap="word")
            version_text.configure(font=("", 18))
            version_text.insert(ctk.END, f"[ERR] {e}")
            return

        metadata_json = json.dumps(metadata, indent=2)
        version_text.configure(state="normal")
        version_text.delete(0.0, ctk.END)
        for line in metadata_json.splitlines():
            version_text.insert(ctk.END, line)
            version_text.insert(ctk.END, "\n")

        version_text.configure(state="disabled")

        metadata_button.configure(state="normal")

    init_thread = threading.Thread(target=init_func)
    init_thread.start()
                    
    version_window.mainloop()

super_index = {}
algs = super_index.keys()

def update_options():
    super_index.clear()

    for button in versions_buttons:
        if button._fg_color == "#242424":
            index = qsb.get_index(version=button.cget("text"))
            for alg in list(index.keys()):
                if alg not in list(algs):
                    super_index[alg] = {}
                size_obj = index[alg]
                for size in size_obj:
                    size = str(size)
                    if size not in list(super_index[alg].keys()):
                        super_index[alg][size] = []
                    backends = size_obj[int(size)]
                    for backend in backends:
                        if backend not in super_index[alg][size]:
                            super_index[alg][size].append(backend)

    if not super_index:
        
        alg_drop.reset()
        alg_drop.set_state("disabled")

        size_drop.reset()
        size_drop.set_state("disabled")

        back_drop.reset()
        back_drop.set_state("disabled")

        return
    
    values = list(algs)
    values.sort()
    
    alg_drop.set_values(values)
    alg_drop.set_state("normal")

    alg = alg_drop.get_value()
    size = size_drop.get_value()
    back = back_drop.get_value()

    if alg not in values:
        alg_drop.reset()

        size_drop.reset()
        size_drop.set_state("disabled")

        back_drop.reset()
        back_drop.set_state("disabled")
    else:
        sizes = list(super_index[alg].keys())
        sizes = list(map(int, sizes))
        sizes.sort()
        sizes = list(map(str, sizes))
        size_drop.set_values(sizes)
        if size not in sizes:
            size_drop.reset()

            back_drop.reset()
            back_drop.set_state("disabled")
        else:
            backs = super_index[alg][size]
            backs.sort()
            back_drop.set_values(backs)
            if back not in backs:
                back_drop.reset()

def version_select(button):
    if button._fg_color == "#3B3B3B":
        button.configure(fg_color="#242424")
    else:
        button.configure(fg_color="#3B3B3B")

    update_options()

def select_all():
    for button in versions_buttons:
        button.configure(fg_color="#242424")
    
    update_options()

select_all_button = ctk.CTkButton(versions_super_frame, text="Select all", command=select_all, border_width=0)
select_all_button.grid(row=1, column=0)

def deselect_all():
    for button in versions_buttons:
        button.configure(fg_color="#3B3B3B")

    update_options()

deselect_all_button = ctk.CTkButton(versions_super_frame, text="Deselect all", command=deselect_all, border_width=0)
deselect_all_button.grid(row=1, column=1)

parameters_frame = ctk.CTkFrame(root, fg_color="#3B3B3B", corner_radius=5)
parameters_frame.grid(row=1, column=2, rowspan=2, sticky="news", padx=10, pady=10)

parameters_frame.rowconfigure(0, weight=1)
parameters_frame.rowconfigure(1, weight=1)
parameters_frame.rowconfigure(2, weight=1)
parameters_frame.rowconfigure(3, weight=1)
parameters_frame.rowconfigure(4, weight=1)
parameters_frame.rowconfigure(5, weight=1)
parameters_frame.rowconfigure(6, weight=1)
parameters_frame.rowconfigure(7, weight=1)
parameters_frame.rowconfigure(8, weight=1)

parameters_frame.columnconfigure(0, weight=1)
parameters_frame.columnconfigure(1, weight=1)

alg_label = ctk.CTkLabel(parameters_frame, text="Algorithm:", fg_color="#3B3B3B")
alg_label.grid(row=0, column=0)

def alg_select():
    alg = alg_drop.get_value()
    values = list(super_index[alg].keys())
    values = list(map(int, values))
    values.sort()
    values = list(map(str, values))

    size_drop.set_values(values)
    size_drop.set_state("normal")

    size = size_drop.get_value()
    back = back_drop.get_value()

    if size not in values:
        size_drop.reset()
        
        back_drop.reset()
        back_drop.set_state("disabled")
    else:
        backs = super_index[alg][size]
        backs.sort()
        back_drop.set_values(backs)
        if back not in backs:
            back_drop.reset()

alg_drop = DropDown(parameters_frame, width=300, border_width=0, state="disabled", command=alg_select)
alg_drop.grid(row=0, column=1)

size_label = ctk.CTkLabel(parameters_frame, text="Size:", fg_color="#3B3B3B")
size_label.grid(row=1, column=0)

def size_select():
    alg = alg_drop.get_value()
    size = size_drop.get_value()
    values = super_index[alg][size]
    values.sort()

    back_drop.set_values(values)
    back_drop.set_state("normal")

    if back_drop.get_value() not in values:
        back_drop.reset

size_drop = DropDown(parameters_frame, width=300, border_width=0, state="disabled", command=size_select)
size_drop.grid(row=1, column=1)

back_label = ctk.CTkLabel(parameters_frame, text="Backend:", fg_color="#3B3B3B")
back_label.grid(row=2, column=0)

back_drop = DropDown(parameters_frame, width=300, border_width=0, state="disabled")
back_drop.grid(row=2, column=1)

shots_label = ctk.CTkLabel(parameters_frame, text="Shots count:", fg_color="#3B3B3B")
shots_label.grid(row=3, column=0)

shots_entry = ctk.CTkEntry(parameters_frame, border_width=0, width=300)
shots_entry.grid(row=3, column=1)

cache_check = ctk.CTkCheckBox(parameters_frame, text="Use cached data", onvalue=False, offvalue=True)
cache_check.select()
cache_check.grid(row=4, column=1)

exact_check = ctk.CTkCheckBox(parameters_frame, text="Exact shots count", onvalue=True, offvalue=False)
exact_check.select()
exact_check.grid(row=4, column=0)

circuit_label = ctk.CTkLabel(parameters_frame, text="Circuit type:", fg_color="#3B3B3B")
circuit_label.grid(row=5, column=0)

circuit_drop = ctk.CTkOptionMenu(parameters_frame, values=["normal", "mirror"], width=300, dynamic_resizing=False)
circuit_drop.grid(row=5, column=1)

strategy_label = ctk.CTkLabel(parameters_frame, text="Sampling strategy:", fg_color="#3B3B3B")
strategy_label.grid(row=6, column=0)

strategy_drop = ctk.CTkOptionMenu(parameters_frame, values=["sequential", "random"], width=300, dynamic_resizing=False)
strategy_drop.grid(row=6, column=1)

seed_label = ctk.CTkLabel(parameters_frame, text="Seed:\n(optional)", fg_color="#3B3B3B")
seed_label.grid(row=7, column=0)

seed_entry = ctk.CTkEntry(parameters_frame, border_width=0, width=300)
seed_entry.grid(row=7, column=1)

def get_samples():
    clear_text()

    alg = alg_drop.get_value()
    size = size_drop.get_value()
    back = back_drop.get_value()
    shots = shots_entry.get()
    exact = exact_check.get()
    cache = cache_check.get()
    circuit = "circuit" if circuit_drop.get() == "normal" else "mirror"
    strategy = strategy_drop.get()
    seed = seed_entry.get() or None
    versions = [button.cget("text") for button in versions_buttons if button._fg_color == "#242424"]

    if not versions or not alg or not size or not back or not size:
        display_error("Missing parameters")
        return

    if not shots.isdigit():
        display_error("Shots count must be a positive integer")
        return
    
    try:
        samples = qsb.get_outcomes(alg, int(size), back, int(shots), circuit, exact=exact, strategy=strategy, versions=versions, seed=seed, force=cache)
    except Exception as e:
        display_error(f"{e}")
        return
    
    now = datetime.now()
    now = now.strftime("%Y-%m-%d_%H-%M-%S")

    path = f"{config['OUTPUT_DIR']}/samples/{now}_{alg}_{size}_{back}.json"

    Path(f"{config['OUTPUT_DIR']}/samples").mkdir(parents=True, exist_ok=True)
    with open(path, "w") as file:
        json.dump(samples, file)

    display_message(f"Samples saved at {path}")
    
sample_img = ctk.CTkImage(dark_image=Image.open("assets/atom_dark.png"), size=(30,30))
sample_button = ctk.CTkButton(parameters_frame, text="Get samples", command=get_samples, image=sample_img, border_width=0)
sample_button.grid(row=8, column=0, columnspan=2)

response_text = ctk.CTkTextbox(root, height=60, width=600, state="disabled", wrap="word")
response_text.grid(row=3, column=0, columnspan=3)
response_text.tag_config("white", foreground="white")
response_text.tag_config("red", foreground="red")

def update_versions():
    for version_button in versions_buttons:
        version_button.destroy()
    versions_buttons.clear()
    
    for version in versions:
        try:
            qsb.get_index(version=version)
        except Exception as e:
            clear_text()
            display_error(f"{e}")
        
        version_button = ctk.CTkButton(versions_frame, text=version, border_width=0, corner_radius=0, fg_color="#3B3B3B", hover_color="#242424")
        version_button.configure(command=lambda b=version_button: version_select(b))
        version_button.bind("<Button-3>", lambda e, v=version: open_version(e, v))
        version_button.pack(fill=ctk.X)
        versions_buttons.append(version_button)

versions = []

def init_func():
    global versions
    global qsb
    display_message("Loading...")
    try:
        import qsimbench as qsb
        versions = qsb.get_versions()
    except Exception as e:
        clear_text()
        display_error(f"{e}")
        return

    update_versions()
    clear_text()
    display_message("Ready!")
    

init_thread = threading.Thread(target=init_func)
init_thread.start()

root.mainloop()