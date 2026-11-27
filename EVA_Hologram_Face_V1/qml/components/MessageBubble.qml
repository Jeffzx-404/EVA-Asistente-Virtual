import QtQuick

Item {
    id: row
    property string speaker: "EVA"
    property string message: ""
    property string stamp: "16:24"
    property bool reminder: false
    property bool highlighted: false
    readonly property bool own: speaker === "TÚ"
    readonly property bool narrow:width<420
    implicitHeight: bubble.height+14
    EvaMark {x:row.narrow?12:22;y:4;width:row.narrow?30:43;height:width;visible:!row.own}
    Rectangle {
        id:bubble
        x:row.own ? row.width-width-(row.narrow?16:26):(row.narrow?52:80)
        width:row.width-(row.narrow?68:(row.own?120:145))
        height:row.reminder ? Math.max(140,reminderCard.y+reminderCard.height+29) : Math.max(row.own ? 50 : row.message.length>100?110:70,body.implicitHeight+(row.own?23:26))
        radius:19
        border.width:1;border.color:row.highlighted?"#83d6ef":row.own?"#6854ae":"#3b4e70"
        gradient: Gradient {
            orientation: row.own ? Gradient.Horizontal:Gradient.Vertical
            GradientStop{position:0;color:row.own?"#48278c":"#ed1c2b48"}
            GradientStop{position:.6;color:row.own?"#2a245c":"#ed15223b"}
            GradientStop{position:1;color:row.own?"#192444":"#ed111e33"}
        }
        Text {
            id:body;x:16;y:12
            width:parent.width-32-(row.own && row.message.length<40?77:0)
            text:row.message;color:"#f7f5ff";font.pixelSize:row.narrow?16:17
            wrapMode:Text.Wrap;lineHeight:1.13
            textFormat:Text.PlainText
        }
        Rectangle {
            id:reminderCard;visible:row.reminder;x:16;y:Math.max(46,body.y+body.implicitHeight+12);width:parent.width-32;height:Math.max(65,reminderDate.y+reminderDate.implicitHeight+10);radius:14
            color:"#c4142540";border.color:"#394c70"
            Icon{x:16;y:10;width:21;height:21;name:"calendar"}
            Text{id:reminderTitle;x:row.narrow?43:51;y:9;width:parent.width-x-40;text:"Reunión del proyecto";font.pixelSize:row.narrow?16:18;font.weight:Font.DemiBold;color:"#f2f1ff";wrapMode:Text.Wrap}
            Icon{x:16;y:reminderDate.y;width:19;height:19;name:"clock";ink:"#c9d9f9"}
            Text{id:reminderDate;x:row.narrow?43:51;y:reminderTitle.y+reminderTitle.implicitHeight+6;width:parent.width-x-12;text:"Mañana a las 10:00 a.m.";font.pixelSize:row.narrow?14:16;color:"#e9edfc";wrapMode:Text.Wrap}
            Icon{x:parent.width-34;y:17;width:24;height:24;name:"check";ink:"#00ee91"}
        }
        Text {anchors.right:parent.right;anchors.rightMargin:14;anchors.bottom:parent.bottom;anchors.bottomMargin:8
            text:row.stamp+(row.own?"  ✓✓":"");font.pixelSize:13;color:"#afc0dc"}
    }
}
