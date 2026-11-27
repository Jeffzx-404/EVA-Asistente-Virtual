import QtQuick
import QtQuick.Controls

Item {
    id: metrics
    property bool horizontal: false
    readonly property real panelGap:horizontal?12:20
    readonly property real cardWidth:horizontal?(width-2*panelGap)/3:width
    readonly property bool tight:cardWidth<320
    readonly property real headerHeight:tight?52:63
    signal detailsRequested(string section)
    GlassPanel {
        id:system;objectName:"systemPanel"
        width:metrics.cardWidth;height:metrics.horizontal?metrics.height:(metrics.height-2*metrics.panelGap)*.387
        Icon {x:metrics.tight?14:26;y:18;width:metrics.tight?24:31;height:width;name:"cpu";ink:"#3ccbe8"}
        Text{x:metrics.tight?48:74;y:21;text:"Sistema";color:"#f0f4ff";font.pixelSize:metrics.tight?17:21;font.weight:Font.DemiBold}
        Rectangle {anchors.right:parent.right;anchors.rightMargin:metrics.tight?12:23;y:18;width:metrics.tight?85:112;height:metrics.tight?25:30;radius:15;color:"#b0103835";border.color:"#293b6259"
            Text{anchors.centerIn:parent;text:"● Operativo";color:"#53dfb3";font.pixelSize:metrics.tight?12:14}}
        Rectangle{x:metrics.tight?14:24;y:metrics.headerHeight;width:parent.width-2*x;height:1;color:"#26384f";opacity:.7}
        Row {id:rings;anchors.horizontalCenter:parent.horizontalCenter;y:metrics.headerHeight+(parent.height-metrics.headerHeight-height)/2;spacing:metrics.tight?8:20
            readonly property real ringSize:Math.min(94,(system.width-28-2*spacing)/3,system.height-metrics.headerHeight-16)
            MetricRing {width:rings.ringSize;height:width;label:"CPU";value:12;accent:"#35d9eb"}
            MetricRing {width:rings.ringSize;height:width;label:"RAM";value:38;accent:"#27b2ec"}
            MetricRing {width:rings.ringSize;height:width;label:"GPU";value:24;accent:"#a16cf0"}
        }
        MouseArea {anchors.fill:parent;hoverEnabled:true;cursorShape:Qt.PointingHandCursor;onClicked:metrics.detailsRequested("Sistema")
            ToolTip.visible:containsMouse;ToolTip.delay:700;ToolTip.text:"Métricas de demostración; no se consulta el equipo"}
    }
    GlassPanel {
        id:network;objectName:"networkPanel"
        x:metrics.horizontal?system.width+metrics.panelGap:0;y:metrics.horizontal?0:system.height+metrics.panelGap
        width:system.width;height:metrics.horizontal?metrics.height:(metrics.height-2*metrics.panelGap)*.323
        readonly property real bodyTop:metrics.headerHeight+(height-metrics.headerHeight-80)/2
        Icon{x:metrics.tight?14:26;y:18;width:metrics.tight?24:32;height:width;name:"wifi";ink:"#3ccbe8";stroke:2.2}
        Text{x:metrics.tight?48:74;y:21;text:"Red";color:"#f0f4ff";font.pixelSize:metrics.tight?17:21;font.weight:Font.DemiBold}
        Rectangle{anchors.right:parent.right;anchors.rightMargin:metrics.tight?12:23;y:18;width:metrics.tight?88:108;height:metrics.tight?25:30;radius:15;color:"#b0103835";border.color:"#293b6259"
            Text{anchors.centerIn:parent;text:"● Conectado";color:"#53dfb3";font.pixelSize:metrics.tight?12:14}}
        Rectangle{x:metrics.tight?14:24;y:metrics.headerHeight;width:parent.width-2*x;height:1;color:"#26384f";opacity:.7}
        Icon{x:metrics.tight?14:30;y:network.bodyTop;width:metrics.tight?20:25;height:width;name:"down";ink:"#43cde5";stroke:2}
        Text{x:metrics.tight?42:73;y:network.bodyTop+2;text:"104.2 Mbps";color:"#e1eafa";font.pixelSize:metrics.tight?15:18}
        Icon{x:metrics.tight?14:30;y:network.bodyTop+41;width:metrics.tight?20:25;height:width;name:"up";ink:"#ac8ae4";stroke:2}
        Text{x:metrics.tight?42:73;y:network.bodyTop+43;text:"48.7 Mbps";color:"#e1eafa";font.pixelSize:metrics.tight?15:18}
        Canvas {
            x:metrics.tight?140:190;y:network.bodyTop;width:parent.width-x-(metrics.tight?12:23);height:69
            onWidthChanged:requestPaint()
            onPaint:{const c=getContext("2d");c.reset();c.scale(width/160,height/69)
                const g=c.createLinearGradient(0,65,160,0);g.addColorStop(0,"#3dcfe5");g.addColorStop(.5,"#537fe6");g.addColorStop(1,"#b582ed")
                c.beginPath();c.moveTo(0,67);c.bezierCurveTo(26,67,31,33,51,42);c.bezierCurveTo(78,58,80,21,101,23);c.bezierCurveTo(122,26,119,35,140,14);c.bezierCurveTo(150,4,155,2,160,1)
                c.strokeStyle=g;c.lineWidth=2;c.stroke();c.lineTo(160,69);c.lineTo(0,69);c.closePath()
                const fill=c.createLinearGradient(0,0,0,69);fill.addColorStop(0,"#554d69b0");fill.addColorStop(1,"#034d69b0");c.fillStyle=fill;c.fill()
            }
        }
        MouseArea{anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:metrics.detailsRequested("Red")}
    }
    GlassPanel {
        objectName:"processPanel"
        x:metrics.horizontal?(system.width+metrics.panelGap)*2:0;y:metrics.horizontal?0:network.y+network.height+metrics.panelGap
        width:system.width;height:metrics.horizontal?metrics.height:metrics.height-y
        bottomColor:"#201841"
        Icon{x:metrics.tight?14:26;y:18;width:metrics.tight?24:31;height:width;name:"layers"}
        Text{x:metrics.tight?48:74;y:21;text:"Procesos";color:"#f0f4ff";font.pixelSize:metrics.tight?17:21;font.weight:Font.DemiBold}
        Text{x:parent.width-(metrics.tight?91:123);y:24;text:"68 activos";color:"#c7d4e9";font.pixelSize:metrics.tight?12:16}
        Icon{x:parent.width-(metrics.tight?27:38);y:24;width:metrics.tight?16:20;height:width;name:"chevron"}
        Rectangle{x:metrics.tight?14:24;y:metrics.headerHeight;width:parent.width-2*x;height:1;color:"#35334f";opacity:.7}
        Row{id:bars;x:metrics.tight?14:30;width:parent.width-2*x;y:metrics.headerHeight+(parent.height-metrics.headerHeight-47)/2;spacing:metrics.tight?3:5
            Repeater {model:[21,25,40,30,31,47,31,29,20,28,31,40,27,29,28,25,21,38,40]
                Rectangle {required property var modelData;width:(bars.width-18*bars.spacing)/19;height:modelData;radius:6;y:47-height
                    gradient:Gradient{GradientStop{position:0;color:"#536ee0"}GradientStop{position:1;color:"#a05de5"}}}
            }
        }
        MouseArea{anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:metrics.detailsRequested("Procesos")}
    }
}
