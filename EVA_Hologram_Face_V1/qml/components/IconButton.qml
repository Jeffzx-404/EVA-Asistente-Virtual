import QtQuick
import QtQuick.Controls
import QtQuick.Window

Button {
    id: button
    property string symbol: "search"
    property string hint: ""
    property color ink: "#eff1ff"
    property bool filled: false
    property bool neon: false
    property real iconSize: 26
    readonly property bool motionAllowed:Window.window && !Window.window.reducedMotion && Window.window.visibility!==Window.Minimized
    implicitWidth:44;implicitHeight:44
    hoverEnabled:true
    focusPolicy:Qt.StrongFocus
    Accessible.name: hint
    ToolTip.visible: hovered && hint.length>0
    ToolTip.text:hint
    ToolTip.delay:600
    background: Rectangle {
        radius:height/2
        border.width: button.filled||button.activeFocus ? 1 : 0
        border.color:button.activeFocus ? "#83d6ef":button.neon?"#6c9be3":"#486387"
        gradient:Gradient {
            GradientStop {position:0;color:button.neon ? "#844fe8" : button.filled ? "#203958":"transparent"}
            GradientStop {position:.58;color:button.neon ? "#365bce" : button.filled ? "#102640":"transparent"}
            GradientStop {position:1;color:button.neon ? "#159ec8" : button.filled ? "#0a1b33":"transparent"}
        }
        Rectangle {
            anchors.fill:parent;anchors.margins:1;radius:parent.radius-1
            color:button.down?"#253146":"#8cbded"
            opacity:button.down?.22:button.hovered?.12:0
            Behavior on opacity {enabled:button.motionAllowed;NumberAnimation{duration:120;easing.type:Easing.OutCubic}}
        }
    }
    contentItem: Item {
        scale:button.down?.96:1
        Behavior on scale {enabled:button.motionAllowed;NumberAnimation{duration:100;easing.type:Easing.OutCubic}}
        Icon {anchors.centerIn:parent;width:button.iconSize;height:width;name:button.symbol;ink:button.ink}
    }
}
