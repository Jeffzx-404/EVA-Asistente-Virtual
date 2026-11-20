import QtQuick
import QtQuick.Controls

Button {
    id: control
    property bool selected: false
    property color accent: "#8d83d8"
    implicitHeight: 40
    implicitWidth: label.implicitWidth + 26
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    Accessible.name: text
    contentItem: Text {
        id: label
        text: control.text
        color: control.selected || control.hovered ? "#f2f1ff" : "#b6c0da"
        font.family: "Segoe UI"
        font.pixelSize: 10
        font.letterSpacing: .8
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
    background: Rectangle {
        radius: 5
        color: control.down ? "#394464" : control.selected ? "#242b48" : (control.hovered ? "#202b42" : "#0b1020")
        Behavior on color { ColorAnimation { duration: 120 } }
        border.width: control.activeFocus ? 2 : 1
        border.color: control.selected || control.activeFocus ? control.accent : "#26304a"
    }
}
