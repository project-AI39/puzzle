# d:/game/puzzle/src/core/state_machine.py
# Core State Machine Logic
# Abstract Base State and Context Manager
# RELEVANT FILES: src/app.py

import abc


class State(abc.ABC):
    def __init__(self, manager):
        self.manager = manager

    def enter(self):
        pass

    def exit(self):
        pass

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass


class StateMachine:
    def __init__(self, app):
        self.app = app
        self.state = None

    def change_state(self, new_state: State):
        if self.state:
            self.state.exit()
        self.state = new_state
        if self.state:
            self.state.enter()

    def handle_event(self, event):
        if self.state:
            self.state.handle_event(event)

    def update(self, dt):
        if self.state:
            self.state.update(dt)

    def draw(self, surface):
        if self.state:
            self.state.draw(surface)
