local ConfirmBox = require("ui/widget/confirmbox")
local Event = require("ui/event")
local InfoMessage = require("ui/widget/infomessage")
local UIManager = require("ui/uimanager")
local WidgetContainer = require("ui/widget/container/widgetcontainer")
local _ = require("gettext")

local Lev = WidgetContainer:extend{
    name = "lev",
    is_doc_only = false,
}

-- The shim (/mnt/app/boordr) reads /tmp/lev-mode after KOReader exits.
local function request(mode, warning)
    UIManager:show(ConfirmBox:new{
        text = warning,
        ok_text = _("Continue"),
        ok_callback = function()
            local f = io.open("/tmp/lev-mode", "w")
            if not f then
                UIManager:show(InfoMessage:new{ text = _("Could not write /tmp/lev-mode.") })
                return
            end
            f:write(mode)
            f:close()
            UIManager:scheduleIn(4, function() UIManager:broadcastEvent(Event:new("Exit")) end)
        end,
    })
end

function Lev:init()
    self.ui.menu:registerToMainMenu(self)
end

function Lev:addToMainMenu(menu_items)
    menu_items.lev = {
        text = _("Lev: USB, ADB, stock reader"),
        sorting_hint = "more_tools",
        sub_item_table = {
            {
                text = _("USB mode (mass storage)"),
                callback = function()
                    request("usb", _("KOReader will close and the Lev becomes a USB drive. Connect the cable; when you unplug it, KOReader comes back. Eject from the PC first. Continue?"))
                end,
            },
            {
                text = _("Enable ADB"),
                callback = function()
                    request("adb", _("KOReader will close and ADB is enabled. When you unplug the cable, KOReader comes back. Continue?"))
                end,
            },
            {
                text = _("Back to the stock reader"),
                callback = function()
                    request("stock", _("KOReader will close and the stock reader takes over (KOReader stays disabled until you delete the .disabled file). Continue?"))
                end,
            },
        },
    }
end

return Lev
