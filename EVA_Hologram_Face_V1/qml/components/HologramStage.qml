import QtQuick
import QtQuick.Effects

Item {
    id: hologram
    // Contrato futuro: animar estas propiedades en el scene graph, sin repintar
    // la interfaz. V1 no mueve el rostro ni simula sincronía de labios.
    property real appearance: 1
    property real speechLevel: 0
    property real lipOpening: 0
    property real headYaw: 0
    property bool paused: false
    property bool reducedQuality: false
    opacity: appearance
    Canvas {
        anchors.fill:parent
        layer.enabled:!hologram.reducedQuality
        layer.effect:MultiEffect{shadowEnabled:true;shadowColor:"#263cff";shadowBlur:.5;shadowOpacity:.9;shadowVerticalOffset:0}
        onWidthChanged:requestPaint()
        onHeightChanged:requestPaint()
        onPaint: {
            const c=getContext("2d");c.reset();c.scale(width/490,height/600)
            function ring(y,rx,ry,tilt){c.save();c.translate(245,y);c.rotate(tilt)
                let g=c.createLinearGradient(-rx,0,rx,0);g.addColorStop(0,"#b52bff");g.addColorStop(.4,"#125fff");g.addColorStop(1,y>300?"#c332ff":"#36f0ff")
                c.strokeStyle=g;c.lineWidth=3;c.beginPath();c.moveTo(-rx,0)
                c.bezierCurveTo(-rx,-ry*.552,-rx*.552,-ry,0,-ry);c.bezierCurveTo(rx*.552,-ry,rx,-ry*.552,rx,0)
                c.bezierCurveTo(rx,ry*.552,rx*.552,ry,0,ry);c.bezierCurveTo(-rx*.552,ry,-rx,ry*.552,-rx,0)
                c.stroke();c.restore()}
            ring(160,222,94,-.28);ring(403,215,82,-.28)
        }
    }
    Image {
        objectName:"facePortrait"
        x:-20;y:0;width:parent.width+40;height:parent.height*1.02
        source:"../../assets/face-hologram.png"
        sourceClipRect: Qt.rect(160,0,1010,1198)
        fillMode:Image.PreserveAspectFit
        smooth:true;asynchronous:true
        transform: Rotation {origin.x:245;origin.y:280;axis.y:1;axis.z:0;angle:hologram.headYaw}
    }
    Canvas {
        x:0;y:parent.height*.88;width:parent.width;height:parent.height*.12
        onPaint: {
            const c=getContext("2d");c.reset();c.scale(width/490,height/72)
            c.save();c.translate(245,32);c.scale(1,.14)
            const glow=c.createRadialGradient(0,0,0,0,0,215);glow.addColorStop(0,"#3edfff");glow.addColorStop(.12,"#006ab5");glow.addColorStop(1,"transparent")
            c.fillStyle=glow;c.fillRect(-220,-220,440,440);c.restore()
            for(let i=0;i<5;i++){c.save();c.translate(245,32);c.scale(1,.14);c.strokeStyle=i===3?"#0265f3":"#0087dc";c.lineWidth=1.3;c.beginPath();c.arc(0,0,62+i*38,0,Math.PI*2);c.stroke();c.restore()}
        }
    }
}
