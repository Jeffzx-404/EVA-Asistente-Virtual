import QtQuick

Canvas {
    property bool wordmark: false
    implicitWidth: wordmark ? 220 : 70
    implicitHeight: 70
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    onPaint: {
        const c=getContext("2d"); c.reset();c.scale(width/(wordmark?220:80),height/80)
        function orbit(rx,ry,rotation,color,line) {
            c.save();c.translate(40,40);c.rotate(rotation);c.scale(1,ry/rx)
            c.beginPath();c.arc(0,0,rx,0,Math.PI*2);c.strokeStyle=color;c.lineWidth=line;c.stroke();c.restore()
        }
        c.shadowColor="#008dff";c.shadowBlur=13
        orbit(33,23,-.65,"#0064dd",4)
        orbit(37,20,-.63,"#00adff",1.6)
        orbit(28,25,-.82,"#6efaff",2.0)
        orbit(35,19,-1.0,"#009dff",1.1)
        if(wordmark) {
            c.shadowBlur=5;c.shadowColor="#8197c1";c.strokeStyle="#f8faff";c.lineWidth=2.6;c.lineCap="round";c.lineJoin="round"
            c.beginPath();c.moveTo(125,28);c.lineTo(110,28);c.bezierCurveTo(101,28,101,52,110,52);c.lineTo(125,52);c.moveTo(104,40);c.lineTo(124,40);c.stroke()
            c.beginPath();c.moveTo(143,28);c.lineTo(157,52);c.lineTo(171,28);c.moveTo(189,52);c.lineTo(202,28);c.lineTo(215,52);c.stroke()
        }
    }
}
