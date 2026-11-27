import QtQuick
import QtQuick.Effects

Item {
    id:pill
    property string status: "HABLANDO"
    Rectangle {x:0;y:5;width:parent.width;height:parent.height;radius:height/2;color:"#2800010b"}
    Rectangle {
        id: borderGlow;anchors.fill:parent;radius:height/2
        gradient:Gradient {orientation:Gradient.Horizontal;GradientStop{position:0;color:"#56d8f4"}GradientStop{position:.48;color:"#6580ee"}GradientStop{position:1;color:"#b471f1"}}
        layer.enabled:true
        layer.effect:MultiEffect {shadowEnabled:true;shadowColor:"#4862ff";shadowOpacity:.35;shadowBlur:.4;shadowVerticalOffset:0}
        Rectangle {anchors.fill:parent;anchors.margins:2;radius:height/2
            gradient:Gradient {orientation:Gradient.Horizontal;GradientStop{position:0;color:"#0e2c4a"}GradientStop{position:.5;color:"#122344"}GradientStop{position:1;color:"#312052"}}
            Rectangle {
                anchors.fill:parent;anchors.margins:1;radius:height/2
                border.width:1;border.color:"#219fc7ef"
                gradient:Gradient {GradientStop{position:0;color:"#188bb8ff"}GradientStop{position:.5;color:"transparent"}GradientStop{position:1;color:"#04003a70"}}
            }
        }
    }
    Row {
        anchors.centerIn:parent;spacing:pill.width<300?12:26
        Item {width:pill.width<300?38:54;height:42
            Row {anchors.centerIn:parent;spacing:4
                Repeater {model:[7,18,33,41,27,15,6];Rectangle{required property var modelData;width:3;height:modelData;radius:2;color:"#d9f5ff";y:(41-height)/2}}
            }
        }
        Text {text:status;color:"#f5f3ff";font.pixelSize:pill.width<300?16:23;font.letterSpacing:pill.width<300?2:4;anchors.verticalCenter:parent.verticalCenter}
    }
}
