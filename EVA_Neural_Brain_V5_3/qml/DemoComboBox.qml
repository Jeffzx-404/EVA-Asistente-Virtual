import QtQuick
import QtQuick.Controls

ComboBox {
    id: box
    implicitHeight: 40
    hoverEnabled: true
    contentItem: Text {
        text: box.displayText; color: "#cad8f0"; font.pixelSize: 11
        leftPadding: 12; rightPadding: 30; verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
    indicator: Text { text: "⌄"; color: "#99acd3"; x: box.width-25; y: 8; font.pixelSize: 18 }
    background: Rectangle {
        radius: 6; color: box.down ? "#26354d" : "#0b1425"
        border.color: box.activeFocus ? "#a59bff" : box.hovered ? "#7385ad" : "#35435f"
        border.width: box.activeFocus ? 2 : 1
    }
    delegate: ItemDelegate {
        required property string modelData
        required property int index
        width: box.width; text: modelData
        contentItem: Text { text: parent.text; color: "#dce5f8"; verticalAlignment: Text.AlignVCenter }
        background: Rectangle { color: parent.highlighted || parent.hovered ? "#293856" : "#101a2e" }
        highlighted: box.highlightedIndex === index
    }
    popup: Popup {
        y: box.height+4; width: box.width; padding: 4
        implicitHeight: contentItem.implicitHeight+8
        contentItem: ListView { implicitHeight: contentHeight; model: box.popup.visible ? box.delegateModel : null; currentIndex: box.highlightedIndex; clip: true }
        background: Rectangle { radius: 6; color: "#101a2e"; border.color: "#58688c" }
    }
}
