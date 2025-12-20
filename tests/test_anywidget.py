import anywidget
import traitlets

from nicegui import ui
from nicegui.testing import Screen


def test_anywidget(screen: Screen):
    events = []

    class CounterWidget(anywidget.AnyWidget):  # pylint: disable=abstract-method
        _esm = '''
            function render({ model, el }) {
                const button = document.createElement("button");
                button.innerHTML = `anywidget: ${model.get("value")}`;
                button.addEventListener("click", () => {
                    model.set("value", model.get("value") + 1);
                    model.save_changes();
                });
                model.on("change:value", () => {
                    button.innerHTML = `anywidget: ${model.get("value")}`;
                    model.send(`value_became_${model.get("value")}`, () => {console.log('message sent')}, [new Uint8Array(4).fill(0xaa).buffer]);
                });
                el.appendChild(button);
            }
            export default { render };
        '''
        value = traitlets.Int(0).tag(sync=True)

    @ui.page('/')
    def page():
        counter = CounterWidget(value=42)
        ui.anywidget(counter).on_message(events.append)

        @ui.button().bind_text_from(counter, 'value', backward=lambda c: f'NiceGUI: {c}').on_click
        def increment_counter() -> None:
            counter.value += 1

    screen.open('/')
    screen.click('anywidget: 42')
    screen.click('NiceGUI: 43')
    screen.should_contain('anywidget: 44')
    for event, expected_value in zip(events, [43, 43, 44], strict=True):
        assert event.content == f'value_became_{expected_value}'
        assert event.buffers is not None
        assert len(event.buffers) == 1
        assert event.buffers[0] == bytes([0xaa, 0xaa, 0xaa, 0xaa])
