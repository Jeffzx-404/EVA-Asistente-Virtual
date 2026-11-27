import QtQuick

Item {
    id: panel
    property real curvature: 24
    property color topColor: "#1b3357"
    property color bottomColor: "#091c36"
    property bool emphasized: false
    // Layered translucent rectangles: no blur texture or full-panel offscreen pass.
    Repeater {
        model:3
        Rectangle {
            required property int index
            x:-index;y:3+index*2;width:panel.width+index*2;height:panel.height
            radius:panel.curvature+index;color:"#12000109"
        }
    }
    Rectangle {
        anchors.fill:parent;radius:panel.curvature
        border.width:1;border.color:panel.emphasized?"#b18fdaf4":"#85668fbc"
        gradient: Gradient {
            GradientStop {position:0;color:Qt.rgba(panel.topColor.r,panel.topColor.g,panel.topColor.b,.88)}
            GradientStop {position:.42;color:"#e609162e"}
            GradientStop {position:1;color:Qt.rgba(panel.bottomColor.r,panel.bottomColor.g,panel.bottomColor.b,.91)}
        }
    }
    Rectangle {
        anchors.fill:parent;anchors.margins:1;radius:panel.curvature-1
        border.width:1;border.color:"#199ebeff"
        gradient:Gradient {
            GradientStop{position:0;color:"#1094c9ff"}
            GradientStop{position:.17;color:"#0394c9ff"}
            GradientStop{position:.45;color:"transparent"}
            GradientStop{position:1;color:"#031a8dd9"}
        }
    }
    Rectangle {
        x:panel.curvature;y:1;width:parent.width-2*panel.curvature;height:1
        gradient:Gradient {
            orientation:Gradient.Horizontal
            GradientStop{position:0;color:"transparent"}
            GradientStop{position:.35;color:"#9698d6ff"}
            GradientStop{position:.72;color:"#468f8ce8"}
            GradientStop{position:1;color:"transparent"}
        }
    }
}
