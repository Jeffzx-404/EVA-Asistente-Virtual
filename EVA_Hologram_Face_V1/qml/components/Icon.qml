import QtQuick

Canvas {
    id: icon
    property string name: "chat"
    property color ink: "#eef0ff"
    property real stroke: 1.6
    implicitWidth: 28; implicitHeight: 28
    onNameChanged: requestPaint()
    onInkChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    onPaint: {
        const c=getContext("2d"); c.reset(); c.scale(width/24,height/24)
        c.strokeStyle=ink; c.fillStyle=ink; c.lineWidth=stroke; c.lineCap="round"; c.lineJoin="round"
        function path(points,closed) { c.beginPath();c.moveTo(points[0][0],points[0][1]);for(let i=1;i<points.length;i++)c.lineTo(points[i][0],points[i][1]);if(closed)c.closePath();c.stroke() }
        function circle(x,y,r,fill) { c.beginPath();c.arc(x,y,r,0,Math.PI*2); if(fill)c.fill();else c.stroke() }
        function rect(x,y,w,h,r) {c.beginPath();c.roundedRect(x,y,w,h,r,r);c.stroke()}
        switch(name) {
        case "chat": rect(2,3,20,15,4); path([[6,18],[4,22],[12,18]],false);[7,12,17].forEach(x=>circle(x,10,0.8,true));break
        case "search": circle(10,10,6);path([[15,15],[21,21]],false);break
        case "grid": [[3,3],[14,3],[3,14],[14,14]].forEach(p=>rect(p[0],p[1],7,7,1));break
        case "layers": path([[2,7],[12,2],[22,7],[12,12]],true);path([[2,12],[12,17],[22,12]],false);path([[2,17],[12,22],[22,17]],false);break
        case "bell": c.beginPath();c.moveTo(3,18);c.quadraticCurveTo(6,16,6,10);c.quadraticCurveTo(6,4,12,4);c.quadraticCurveTo(18,4,18,10);c.quadraticCurveTo(18,16,21,18);c.closePath();c.stroke();path([[12,2],[12,4]],false);c.beginPath();c.arc(12,20,2,0,Math.PI);c.stroke();break
        case "sliders": [5,12,19].forEach((y,i)=>{path([[2,y],[22,y]],false);c.fillStyle="#0b122a";circle([16,7,14][i],y,2,true);circle([16,7,14][i],y,2,false)});break
        case "person": circle(12,7,4);c.beginPath();c.moveTo(4,21);c.bezierCurveTo(4,12,20,12,20,21);c.stroke();break
        case "settings": for(let i=0;i<8;i++){let a=i*Math.PI/4;c.save();c.translate(12,12);c.rotate(a);rect(-2,-10,4,5,1);c.restore()}circle(12,12,6);circle(12,12,2.5);break
        case "cpu": rect(5,5,14,14,2);[7,12,17].forEach(t=>{path([[t,1],[t,4]],false);path([[t,20],[t,23]],false);path([[1,t],[4,t]],false);path([[20,t],[23,t]],false)});break
        case "wifi": [12,8,4].forEach(r=>{c.beginPath();c.arc(12,20,r,Math.PI*1.22,Math.PI*1.78);c.stroke()});circle(12,21,1.5,true);break
        case "down":path([[12,3],[12,20],[6,14]],false);path([[12,20],[18,14]],false);break
        case "up":path([[12,21],[12,4],[6,10]],false);path([[12,4],[18,10]],false);break
        case "download":path([[12,2],[12,15],[7,10]],false);path([[12,15],[17,10]],false);path([[4,15],[4,21],[20,21],[20,15]],false);break
        case "more":[4,12,20].forEach(x=>circle(x,12,1.3,true));break
        case "chevron":path([[9,5],[16,12],[9,19]],false);break
        case "check":circle(12,12,9);path([[7,12],[11,16],[17,8]],false);break
        case "calendar":rect(3,5,18,16,2);path([[3,10],[21,10]],false);path([[8,2],[8,7]],false);path([[16,2],[16,7]],false);[8,12,16].forEach(x=>[13,17].forEach(y=>circle(x,y,.65,true)));break
        case "clock":circle(12,12,9);path([[12,6],[12,12],[16,14]],false);break
        case "send":path([[2,10],[22,2],[15,22],[11,14],[2,10]],false);path([[11,14],[22,2]],false);break
        case "mic":rect(8,2,8,14,4);c.beginPath();c.moveTo(4,11);c.bezierCurveTo(4,23,20,23,20,11);c.stroke();path([[12,20],[12,24]],false);path([[8,24],[16,24]],false);break
        case "clip":c.beginPath();c.moveTo(11,17);c.lineTo(18,10);c.bezierCurveTo(24,4,17,-1,12,4);c.lineTo(3,13);c.bezierCurveTo(-3,20,5,27,11,21);c.lineTo(20,12);c.moveTo(7,16);c.lineTo(15,8);c.bezierCurveTo(18,5,20,8,17,11);c.lineTo(11,17);c.stroke();break
        case "close":path([[5,5],[19,19]],false);path([[19,5],[5,19]],false);break
        }
    }
}
