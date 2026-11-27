import QtQuick

Canvas {
    onWidthChanged:requestPaint()
    onHeightChanged:requestPaint()
    onPaint: {
        const c=getContext("2d");c.reset();c.scale(width/1672,height/941)
        let base=c.createLinearGradient(0,0,1672,941);base.addColorStop(0,"#040918");base.addColorStop(.5,"#020d20");base.addColorStop(1,"#040c25")
        c.fillStyle=base;c.fillRect(0,0,1672,941)
        function haze(x,y,r,color) {let g=c.createRadialGradient(x,y,0,x,y,r);g.addColorStop(0,color);g.addColorStop(1,"transparent");c.fillStyle=g;c.fillRect(x-r,y-r,r*2,r*2)}
        haze(1080,450,380,"#08203b");haze(40,770,270,"#15245f");haze(1540,850,350,"#11134c")
        function ribbon(top) {
            let g=c.createLinearGradient(0,0,1000,600);g.addColorStop(0,"#247eff");g.addColorStop(.3,"#226aff");g.addColorStop(.7,"#691bfa");g.addColorStop(1,"#001327")
            c.strokeStyle=g;c.lineWidth=1.4
            c.beginPath();if(top){c.moveTo(550,-20);c.bezierCurveTo(710,90,840,28,1000,92)}else{c.moveTo(-20,811);c.bezierCurveTo(160,906,220,877,340,950)}
            for(const line of [50,30,16,7]){c.globalAlpha=.07;c.lineWidth=line;c.stroke()}
            c.globalAlpha=1;c.lineWidth=1.4;c.stroke()
            for(let i=0;i<22;i++){c.globalAlpha=.055;c.beginPath();if(top){c.moveTo(555-i*7,-30);c.bezierCurveTo(700,100-i,850,15,1000,92)}else{c.moveTo(-30,810-i*4);c.bezierCurveTo(80,890,240,875,340,950)}c.stroke()}c.globalAlpha=1
        }
        ribbon(true);ribbon(false)
        c.beginPath();c.moveTo(1100,835);c.bezierCurveTo(1300,695,1480,699,1695,786);c.strokeStyle="#5d39ff";c.lineWidth=1;c.stroke()
        haze(1600,778,170,"#241151");haze(570,4,150,"#104786")
    }
}
