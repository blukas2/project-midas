from unittest.mock import Mock

from ui.dialogs import ThemedMessageBox


class TestThemedMessageBox:
    def test_showerror_builds_and_waits_for_customtkinter_dialog(self, monkeypatch):
        dialog = Mock()
        button = Mock()
        monkeypatch.setattr("ui.dialogs.ctk.CTkToplevel", Mock(return_value=dialog))
        monkeypatch.setattr("ui.dialogs.ctk.CTkLabel", Mock())
        button_factory = Mock(return_value=button)
        monkeypatch.setattr("ui.dialogs.ctk.CTkButton", button_factory)
        parent = Mock()

        ThemedMessageBox.showerror("Error", "Something went wrong.", parent)

        dialog.title.assert_called_once_with("Error")
        dialog.transient.assert_called_once_with(parent)
        dialog.grab_set.assert_called_once_with()
        dialog.wait_window.assert_called_once_with()
        assert button_factory.call_args.kwargs["text"] == "OK"
