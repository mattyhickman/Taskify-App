# Packages and dependencies
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.pickers import MDDatePicker

from kivymd.uix.list import TwoLineAvatarIconListItem, ILeftBodyTouch
from kivymd.uix.selectioncontrol import MDCheckbox

from datetime import datetime

from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.textfield import MDTextField

from database import Database

db = Database()

# Create the login screen
class LoginScreen(Screen):
    def attempt_login(self, username, password):
        user = db.authenticate_user(username, password)
        if user:
            app = MDApp.get_running_app()
            app.user_id = user[0]  # Store the logged-in user's ID
            app.root.current = 'main'
        else:
            self.ids.login_message.text = "Login failed. Please check your username and password."

    def open_register_dialog(self):
        if not hasattr(self, 'register_dialog'):
            self.register_dialog = MDDialog(
                title="Register",
                type="custom",
                content_cls=RegisterContent(),
                buttons=[
                    MDRaisedButton(
                        text="REGISTER",
                        on_release=self.register_user
                    ),
                    MDFlatButton(
                        text="CANCEL",
                        on_release=self.close_register_dialog
                    ),
                ],
            )
        self.register_dialog.open()

    def register_user(self, *args):
        register_content = self.register_dialog.content_cls
        username = register_content.ids.username.text
        password = register_content.ids.password.text

        if username and password:
            try:
                db.create_user(username, password)
                self.ids.login_message.text = "Registration successful! You can now log in."
                self.close_register_dialog()
            except Exception as e:
                self.ids.login_message.text = f"Registration failed: {str(e)}"
        else:
            self.ids.login_message.text = "Please enter both a username and password."

    def close_register_dialog(self, *args):
        self.register_dialog.dismiss()

class RegisterContent(MDBoxLayout):
    pass

    def validate_user(self):
        if db.login_user(self.username.text, self.password.text):
            self.manager.current = "main"  # Switch to the main screen
        else:
            print("Invalid credentials")  # Add proper feedback for invalid login

# Create the registration screen
class RegisterScreen(Screen):
    username = ObjectProperty(None)
    password = ObjectProperty(None)

    def register(self):
        if db.register_user(self.username.text, self.password.text):
            print("User registered successfully")
            self.manager.current = "login"  # Switch to the login screen
        else:
            print("Username already exists")

# Main task screen (existing code)
class MainScreen(Screen):
    pass

class DialogContent(MDBoxLayout):
    """Opens a Dialog Box That Gets The Task From The User"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ids.date_text.text = str(datetime.now().strftime('%A %d %B %Y'))

    #This function will show the date picker
    def show_date_picker(self):
        """Opens the date picker"""
        date_dialog = MDDatePicker()
        date_dialog.bind(on_save=self.on_save)
        date_dialog.open()

    #This function will get the date and save it in a good form
    def on_save(self, instance, value, date_range):
        date = value.strftime('%A %d %B %Y')
        self.ids.date_text.text = str(date)

# Class for marking and deleting the list item
class ListItemWithCheckbox(TwoLineAvatarIconListItem):
    def __init__(self, pk=None, **kwargs):
        super().__init__(**kwargs)
        self.pk = pk

    # Marking the item as complete or incomplete
    def mark(self, check, the_list_item):
        '''Mark the task as complete or incomplete'''
        app = MDApp.get_running_app()  # Get the running app instance
        if check.active:
            the_list_item.text = '[s]' + the_list_item.text + '[/s]'
            db.mark_task_as_complete(app.user_id, self.pk)  # Pass the user ID and task ID
        else:
            the_list_item.text = str(db.mark_task_as_incomplete(app.user_id, self.pk))  # Pass the user ID and task ID

    # Deleting the list item
    def delete_item(self, the_list_item):
        '''Delete the task'''
        app = MDApp.get_running_app()  # Get the running app instance
        self.parent.remove_widget(the_list_item)
        db.delete_task(app.user_id, self.pk)  # Pass the user ID and task ID

class LeftCheckbox(ILeftBodyTouch, MDCheckbox):
    '''Custom left container'''


#This is the main App class
class MainApp(MDApp):
    task_list_dialog = None
    user_id = None

    def login_user(self, username, password):
        user = db.authenticate_user(username, password)
        if user:
            self.user_id = user[0]  # Store the user ID
            self.load_tasks()  # Load tasks after successful login
        else:
            print("Login failed")

    def load_tasks(self):
        incompleted_tasks, completed_tasks = db.get_tasks(self.user_id)
        # Clear existing tasks in the UI and reload them from the database
        self.root.ids.container.clear_widgets()

        for task in incompleted_tasks:
            add_task = ListItemWithCheckbox(pk=task[0], text=str(task[1]), secondary_text=task[2])
            self.root.ids.container.add_widget(add_task)

        for task in completed_tasks:
            add_task = ListItemWithCheckbox(pk=task[0], text='[s]' + str(task[1]) + "[/s]", secondary_text=task[2])
            add_task.ids.check.active = True
            self.root.ids.container.add_widget(add_task)


    #This is the build function for setting the theme
    def build(self):
        self.theme_cls.primary_palette = "Yellow"

        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(RegisterScreen(name="register"))
        sm.add_widget(MainScreen(name="main"))
        return sm


    #This is the show task function
    def show_task_dialog(self):
        if not self.task_list_dialog:
            self.task_list_dialog = MDDialog(
                title="Create Task",
                type="custom",
                content_cls=DialogContent(),
            )

            self.task_list_dialog.open()
    def on_start(self):
        # Load tasks if user_id is set
        if self.user_id is not None:
            incompleted_tasks, completed_tasks = db.get_tasks(self.user_id)
            self.root.ids.container.clear_widgets()
            for task in incompleted_tasks:
                add_task = ListItemWithCheckbox(pk=task[0], text=str(task[1]), secondary_text=task[2])
                self.root.ids.container.add_widget(add_task)
            for task in completed_tasks:
                add_task = ListItemWithCheckbox(pk=task[0], text='[s]' + str(task[1]) + "[/s]", secondary_text=task[2])
                add_task.ids.check.active = True
                self.root.ids.container.add_widget(add_task)

        # This is a dialog closing function
    def close_dialog(self, *args):
        self.task_list_dialog.dismiss()

    #Adding tasks
    def add_task(self, task, task_date):
        main_screen = self.root.get_screen('main')
        created_task = db.create_task(self.user_id, task.text, task_date)

        main_screen.ids['container'].add_widget(
            ListItemWithCheckbox(
                pk=created_task[0],
                text='[b]' + str(created_task[1]) + '[/b]',
                secondary_text=created_task[2]
            )
        )
        task.text = ''

    def mark_task_as_complete(self, user_id, taskid):
        self.cursor.execute("UPDATE tasks SET completed=1 WHERE id=? AND user_id=?", (taskid, user_id))
        self.con.commit()

    def mark_task_as_incomplete(self, taskid):
        db.mark_task_as_incomplete(self.user_id, taskid)

    def delete_task(self, user_id, taskid):
        self.cursor.execute("DELETE FROM tasks WHERE id=? AND user_id=?", (taskid, user_id))
        self.con.commit()

if __name__ == '__main__':
    app = MainApp()
    app.run()