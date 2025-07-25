class ColorBar(HorizontalGroup, can_focus=True):
    BINDINGS = [("left", "decrease", "Decrease value"), ("right", "increase", "Increase value")]
    
    def __init__(self):
        super().__init__()
        self.bar = ProgressBar(total=255, show_percentage=False, show_eta=False)
        self.styles.width = "auto"

    def action_decrease(self):
        if self.bar.progress > 0:
            self.bar.advance(-1)

    def action_increase(self) -> None:
        if self.bar.progress < 255:
            self.bar.advance(1)
    
    def compose(self) -> ComposeResult:
        yield self.bar

class ColorPicker(VerticalGroup):
    def __init__(self):
        super().__init__()
        self.red: ColorBar = ColorBar()
        self.green: ColorBar = ColorBar()
        self.blue: ColorBar = ColorBar()

        self.color = Static("█████████")
        self.colorvalue = [int, int, int]

        self.set = Button("Set Color")

        self.styles.width = "auto"
        self.styles.border = ("round", "white")
        self.styles.padding = (1, 1)

    async def read_color(self):
        while True:
            self.color.styles.color = Color(int(self.red.bar.progress), int(self.green.bar.progress), int(self.blue.bar.progress))
            await asyncio.sleep(0.1)

    async def get_color(self):
        old_color = self.colorvalue
        while self.colorvalue == old_color:
            await asyncio.sleep(0.1)
        return self.colorvalue

    async def on_mount(self):
        self.run_worker(self.read_color(), exclusive=False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.colorvalue = [int(self.red.bar.progress), int(self.green.bar.progress), int(self.blue.bar.progress)]

    def compose(self) -> ComposeResult:
        yield self.red
        yield self.green
        yield self.blue
        yield self.color
        yield self.set

class PopupScreen(Screen):
    def __init__(self, widget):
        super().__init__()
        self.styles.align = ("center", "middle")
        self.styles.background = "black 20%"
        self.popup_widget = widget

    def compose(self) -> ComposeResult:
        yield self.popup_widget

class PickColor(Button):
    def __init__(self, device: Device):
        super().__init__()
        self.device: Device = device
        self.colorpicker = ColorPicker()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        await app.push_screen(PopupScreen(self.colorpicker))
        color = await self.colorpicker.get_color()
        await self.device.run_service("turn_on", data={"rgb_color": color})
        await app.pop_screen()

