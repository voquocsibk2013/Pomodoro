import tkinter as tk
from tkinter import simpledialog, messagebox, Listbox
import threading
import time
import json
from playsound import playsound

class TaskManager:
    def __init__(self, filename='tasks.json'):
        self.filename = filename
        self.tasks = self.load_tasks()

    def reset_session_count(self, task_index):
        """Resets the session count for a task specified by its index."""
        if 0 <= task_index < len(self.tasks):
            self.tasks[task_index]["sessions"] = 0
            self.save_tasks()


    def load_tasks(self):
        try:
            with open(self.filename, 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_tasks(self):
        with open(self.filename, 'w') as file:
            json.dump(self.tasks, file, indent=4)

    def add_task(self, task_name):
        self.tasks.append({"name": task_name, "sessions": 0})
        self.save_tasks()

    def remove_task(self, task_index):
        if 0 <= task_index < len(self.tasks):
            self.tasks.pop(task_index)
            self.save_tasks()

class PomodoroApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Pomodoro Task Manager")
        self.task_manager = TaskManager()
        self.current_task_index = None
        self.create_widgets()
        self.update_tasks_listbox()
        self.stop_timer = threading.Event()
        self.pomodoro_thread = None
        self.break_thread = None

        self.setup_ui()

    def setup_ui(self):
        # Setup other UI components...
        reset_counter_button = tk.Button(self, text="Reset Counter", command=self.reset_counter)
        reset_counter_button.pack(side=tk.LEFT, padx=5, pady=10)

    def reset_counter(self):
        selected_index = self.tasks_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("Reset Counter", "Please select a task to reset its counter.")
            return
        # Perform the reset operation
        self.task_manager.reset_session_count(selected_index[0])
        self.update_tasks_listbox()  # Refresh the task list to show the updated counter
        messagebox.showinfo("Reset Counter", "The session counter has been reset.")



    def create_widgets(self):
        self.tasks_listbox = Listbox(self)
        self.tasks_listbox.pack(padx=10, pady=10)

        tk.Button(self, text="Add Task", command=self.add_task).pack(side=tk.LEFT, padx=(10, 5), pady=10)
        tk.Button(self, text="Remove Selected Task", command=self.remove_task).pack(side=tk.LEFT, padx=5, pady=10)
        self.start_pomodoro_button = tk.Button(self, text="Start Pomodoro", command=self.start_pomodoro)
        self.start_pomodoro_button.pack(side=tk.LEFT, padx=5, pady=10)
        self.stop_pomodoro_button = tk.Button(self, text="Stop Pomodoro", state=tk.DISABLED, command=self.stop_timer_action)
        self.stop_pomodoro_button.pack(side=tk.LEFT, padx=5, pady=10)

        self.timer_label = tk.Label(self, text="Timer: --:--")
        self.timer_label.pack(pady=(10, 0))

    def update_tasks_listbox(self):
        self.tasks_listbox.delete(0, tk.END)
        for task in self.task_manager.tasks:
            self.tasks_listbox.insert(tk.END, f"{task['name']} - Sessions: {task['sessions']}")

    def add_task(self):
        task_name = simpledialog.askstring("Add Task", "Task name:")
        if task_name:
            self.task_manager.add_task(task_name)
            self.update_tasks_listbox()

    def remove_task(self):
        selected_indices = self.tasks_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Remove Task", "Please select a task to remove.")
            return
        for index in selected_indices[::-1]:
            self.task_manager.remove_task(index)
        self.update_tasks_listbox()

    def start_pomodoro(self, duration_minutes=25):
        selected_index = self.tasks_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("Start Pomodoro", "Please select a task to start Pomodoro for.")
            return
        self.current_task_index = selected_index[0]
        task_name = self.task_manager.tasks[self.current_task_index]["name"]

        self.stop_timer.clear()
        self.pomodoro_thread = threading.Thread(target=self.run_pomodoro, args=(duration_minutes, self.current_task_index, task_name))
        self.pomodoro_thread.start()
        self.start_pomodoro_button.config(state=tk.DISABLED)
        self.stop_pomodoro_button.config(state=tk.NORMAL)

    def run_pomodoro(self, duration_minutes, task_index, task_name):
        total_seconds = duration_minutes * 60
        while total_seconds > 0 and not self.stop_timer.is_set():
            mins, secs = divmod(total_seconds, 60)
            timer_text = f"Timer: {mins:02d}:{secs:02d} - {task_name}"
            self.timer_label.config(text=timer_text)
            time.sleep(1)
            total_seconds -= 1
        if not self.stop_timer.is_set():
            playsound('alarm_sound.mp3', block=False)
            # Update the session count immediately after the session ends, before the break logic
            self.task_manager.tasks[task_index]["sessions"] += 1
            self.task_manager.save_tasks()
            self.after(0, self.prompt_session_end_options)
        self.after(0, self.reset_pomodoro_ui)


    def prompt_session_end_options(self):
        response = messagebox.askyesno("Pomodoro Finished", "Would you like to take a break?")
        if response:
            break_duration = simpledialog.askinteger("Break Time", "How many minutes for the break?", minvalue=1, maxvalue=60)
            if break_duration:
                self.run_break(break_duration)
        else:
            self.reset_pomodoro_ui()

    def run_break(self, break_duration):
        self.stop_timer.clear()  # Ensure stop_timer is reset for the break
        self.break_thread = threading.Thread(target=self.break_timer, args=(break_duration,))
        self.break_thread.start()

    def break_timer(self, break_duration):
        total_seconds = break_duration * 60
        while total_seconds > 0 and not self.stop_timer.is_set():
            mins, secs = divmod(total_seconds, 60)
            timer_text = f"Break: {mins:02d}:{secs:02d}"
            self.timer_label.config(text=timer_text)
            time.sleep(1)
            total_seconds -= 1
        if not self.stop_timer.is_set():
            playsound('break_end.mp3', block=False)
        self.after(0, self.reset_pomodoro_ui)


    # def stop_timer_action(self):
    #     self.stop_timer.set()
    #     if self.pomodoro_thread and self.pomodoro_thread.is_alive():
    #         self.pomodoro_thread.join()
    #     if self.break_thread and self.break_thread.is_alive():
    #         self.break_thread.join()
    #     self.reset_pomodoro_ui()
    def stop_timer_action(self):
        self.stop_timer.set()
        # Removed the join() calls to prevent freezing
        self.reset_pomodoro_ui()

    def reset_pomodoro_ui(self):
        self.timer_label.config(text="Timer: --:--")
        self.start_pomodoro_button.config(state=tk.NORMAL)
        self.stop_pomodoro_button.config(state=tk.DISABLED)
        self.update_tasks_listbox()
        self.current_task_index = None

if __name__ == "__main__":
    app = PomodoroApp()
    app.mainloop()
