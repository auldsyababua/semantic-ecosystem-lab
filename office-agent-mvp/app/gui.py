"""Tkinter GUI for Office Assistant MVP."""
import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
from . import llm_client
from . import office_actions


class OfficeAssistantGUI:
    """Main GUI class for Office Assistant."""

    def __init__(self, root):
        """Initialize the GUI."""
        self.root = root
        self.root.title("Office Assistant MVP")
        self.root.geometry("800x600")

        # In-memory message history
        self.messages = []

        # Create GUI components
        self._create_widgets()

    def _create_widgets(self):
        """Create all GUI widgets."""
        # Chat history area
        history_frame = tk.Frame(self.root)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(history_frame, text="Chat History", font=("Arial", 12, "bold")).pack(anchor=tk.W)

        self.chat_display = scrolledtext.ScrolledText(
            history_frame,
            wrap=tk.WORD,
            width=80,
            height=20,
            state=tk.DISABLED,
            font=("Arial", 10)
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=5)

        # Input area
        input_frame = tk.Frame(self.root)
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(input_frame, text="Your message:", font=("Arial", 10)).pack(anchor=tk.W)

        self.input_box = tk.Text(input_frame, height=3, font=("Arial", 10))
        self.input_box.pack(fill=tk.X, pady=5)
        self.input_box.bind("<Return>", lambda e: self._on_send() if not e.state & 0x1 else None)

        self.send_button = tk.Button(
            input_frame,
            text="Send",
            command=self._on_send,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5
        )
        self.send_button.pack(pady=5)

        # Action buttons
        actions_frame = tk.Frame(self.root, bg="#f0f0f0")
        actions_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(
            actions_frame,
            text="Quick Actions",
            font=("Arial", 11, "bold"),
            bg="#f0f0f0"
        ).pack(pady=5)

        buttons_frame = tk.Frame(actions_frame, bg="#f0f0f0")
        buttons_frame.pack()

        # Four action buttons
        self.btn_powerpoint = tk.Button(
            buttons_frame,
            text="Generate PowerPoint",
            command=self._on_generate_powerpoint,
            bg="#E67E22",
            fg="white",
            font=("Arial", 9, "bold"),
            padx=10,
            pady=8
        )
        self.btn_powerpoint.grid(row=0, column=0, padx=5, pady=5)

        self.btn_word = tk.Button(
            buttons_frame,
            text="Draft Word Report",
            command=self._on_draft_word,
            bg="#2E86C1",
            fg="white",
            font=("Arial", 9, "bold"),
            padx=10,
            pady=8
        )
        self.btn_word.grid(row=0, column=1, padx=5, pady=5)

        self.btn_summarize_excel = tk.Button(
            buttons_frame,
            text="Summarize Excel",
            command=self._on_summarize_excel,
            bg="#27AE60",
            fg="white",
            font=("Arial", 9, "bold"),
            padx=10,
            pady=8
        )
        self.btn_summarize_excel.grid(row=0, column=2, padx=5, pady=5)

        self.btn_generate_excel = tk.Button(
            buttons_frame,
            text="Generate Excel File",
            command=self._on_generate_excel,
            bg="#8E44AD",
            fg="white",
            font=("Arial", 9, "bold"),
            padx=10,
            pady=8
        )
        self.btn_generate_excel.grid(row=0, column=3, padx=5, pady=5)

    def _add_to_chat(self, role, content):
        """Add a message to chat history."""
        self.chat_display.config(state=tk.NORMAL)

        if role == "user":
            self.chat_display.insert(tk.END, "You: ", "bold")
            self.chat_display.insert(tk.END, f"{content}\n\n")
        elif role == "assistant":
            self.chat_display.insert(tk.END, "Assistant: ", "bold_blue")
            self.chat_display.insert(tk.END, f"{content}\n\n")
        elif role == "system":
            self.chat_display.insert(tk.END, "System: ", "bold_red")
            self.chat_display.insert(tk.END, f"{content}\n\n")

        # Configure tags
        self.chat_display.tag_config("bold", font=("Arial", 10, "bold"))
        self.chat_display.tag_config("bold_blue", font=("Arial", 10, "bold"), foreground="blue")
        self.chat_display.tag_config("bold_red", font=("Arial", 10, "bold"), foreground="red")

        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def _on_send(self):
        """Handle send button click."""
        user_input = self.input_box.get("1.0", tk.END).strip()

        if not user_input:
            return

        # Clear input box
        self.input_box.delete("1.0", tk.END)

        # Add user message to chat
        self._add_to_chat("user", user_input)

        # Add to messages history
        self.messages.append({"role": "user", "content": user_input})

        # Disable send button while processing
        self.send_button.config(state=tk.DISABLED)

        # Process in background thread
        def process():
            try:
                response = llm_client.chat(self.messages)
                self.messages.append({"role": "assistant", "content": response})

                # Update GUI in main thread
                self.root.after(0, lambda: self._add_to_chat("assistant", response))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.root.after(0, lambda: self.send_button.config(state=tk.NORMAL))

        thread = threading.Thread(target=process, daemon=True)
        thread.start()

    def _on_generate_powerpoint(self):
        """Handle Generate PowerPoint button."""
        user_input = self.input_box.get("1.0", tk.END).strip()

        if not user_input:
            messagebox.showwarning("Input Required", "Please enter a prompt for PowerPoint generation.")
            return

        # Clear input box
        self.input_box.delete("1.0", tk.END)

        # Add to chat
        self._add_to_chat("user", f"[Generate PowerPoint] {user_input}")

        # Disable buttons
        self._disable_action_buttons()

        # Process in background
        def process():
            try:
                result = office_actions.generate_powerpoint_from_prompt(user_input)
                self.root.after(0, lambda: self._add_to_chat("system", result))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.root.after(0, self._enable_action_buttons)

        thread = threading.Thread(target=process, daemon=True)
        thread.start()

    def _on_draft_word(self):
        """Handle Draft Word Report button."""
        user_input = self.input_box.get("1.0", tk.END).strip()

        if not user_input:
            messagebox.showwarning("Input Required", "Please enter a prompt for Word report generation.")
            return

        # Clear input box
        self.input_box.delete("1.0", tk.END)

        # Add to chat
        self._add_to_chat("user", f"[Draft Word Report] {user_input}")

        # Disable buttons
        self._disable_action_buttons()

        # Process in background
        def process():
            try:
                result = office_actions.draft_word_report(user_input)
                self.root.after(0, lambda: self._add_to_chat("system", result))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.root.after(0, self._enable_action_buttons)

        thread = threading.Thread(target=process, daemon=True)
        thread.start()

    def _on_summarize_excel(self):
        """Handle Summarize Excel button."""
        user_input = self.input_box.get("1.0", tk.END).strip()

        if not user_input:
            messagebox.showwarning("Input Required", "Please enter a prompt for Excel summarization.")
            return

        # Clear input box
        self.input_box.delete("1.0", tk.END)

        # Add to chat
        self._add_to_chat("user", f"[Summarize Excel] {user_input}")

        # Disable buttons
        self._disable_action_buttons()

        # Process in background
        def process():
            try:
                result = office_actions.summarize_excel(user_input)
                self.root.after(0, lambda: self._add_to_chat("assistant", result))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.root.after(0, self._enable_action_buttons)

        thread = threading.Thread(target=process, daemon=True)
        thread.start()

    def _on_generate_excel(self):
        """Handle Generate Excel File button."""
        user_input = self.input_box.get("1.0", tk.END).strip()

        if not user_input:
            messagebox.showwarning("Input Required", "Please enter a prompt for Excel file generation.")
            return

        # Clear input box
        self.input_box.delete("1.0", tk.END)

        # Add to chat
        self._add_to_chat("user", f"[Generate Excel File] {user_input}")

        # Disable buttons
        self._disable_action_buttons()

        # Process in background
        def process():
            try:
                result = office_actions.generate_excel_file_from_prompt(user_input)
                self.root.after(0, lambda: self._add_to_chat("system", result))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.root.after(0, self._enable_action_buttons)

        thread = threading.Thread(target=process, daemon=True)
        thread.start()

    def _disable_action_buttons(self):
        """Disable all action buttons during processing."""
        self.btn_powerpoint.config(state=tk.DISABLED)
        self.btn_word.config(state=tk.DISABLED)
        self.btn_summarize_excel.config(state=tk.DISABLED)
        self.btn_generate_excel.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)

    def _enable_action_buttons(self):
        """Enable all action buttons after processing."""
        self.btn_powerpoint.config(state=tk.NORMAL)
        self.btn_word.config(state=tk.NORMAL)
        self.btn_summarize_excel.config(state=tk.NORMAL)
        self.btn_generate_excel.config(state=tk.NORMAL)
        self.send_button.config(state=tk.NORMAL)
