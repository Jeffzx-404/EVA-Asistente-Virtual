import QtQuick

Item {
    objectName:"metric-"+label
    property string label: "CPU"
    property int value: 12
    property color accent: "#00eaff"
    width:94;height:94
    Canvas {
        anchors.fill:parent
        onWidthChanged:requestPaint();onHeightChanged:requestPaint()
        onPaint: {
            const c=getContext("2d");c.reset();c.lineWidth=8;c.lineCap="round"
            const r=width/2-6
            c.strokeStyle="#253550";c.beginPath();c.arc(width/2,height/2,r,0,Math.PI*2);c.stroke()
            c.strokeStyle=accent;c.beginPath();c.arc(width/2,height/2,r,-Math.PI/2,-Math.PI/2+Math.PI*2*value/100);c.stroke()
        }
    }
    Text {anchors.horizontalCenter:parent.horizontalCenter;y:parent.height/2-(parent.width<70?16:22);text:label;color:"#bbcce3";font.pixelSize:parent.width<70?12:14}
    Text {anchors.horizontalCenter:parent.horizontalCenter;y:parent.height/2+1;text:value+"%";color:"#f1f6ff";font.pixelSize:parent.width<70?17:21;font.weight:Font.Medium}
}
