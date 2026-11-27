import QtQuick
import QtQuick.Controls

GlassPanel {
    id:panel
    property alias messageModel: messages
    property string page: "Conversación"
    property int foundIndex: -1
    property bool reducedMotion:false
    readonly property bool narrow:width<420
    readonly property bool compressed:height<420
    signal reducedMotionRequested(bool value)
    signal exportRequested(string transcript)
    signal notice(string message)
    curvature:24;topColor:"#25365e";bottomColor:"#0a2342"
    function addMessage(value) {
        const clean=value.trim();if(!clean)return false
        const stamp=Qt.formatTime(new Date(),"hh:mm")
        messages.append({speaker:"TÚ",message:clean,stamp:stamp,reminder:false})
        messages.append({speaker:"EVA",message:"Mensaje recibido en esta demostración. La conversación real se conectará en una fase posterior.",stamp:stamp,reminder:false})
        Qt.callLater(()=>chat.positionViewAtEnd());return true
    }
    function findMessage(term) {
        foundIndex=-1
        for(let i=0;i<messages.count;i++)if(messages.get(i).message.toLowerCase().indexOf(term.toLowerCase())>=0){foundIndex=i;break}
        if(foundIndex>=0)Qt.callLater(()=>chat.positionViewAtIndex(foundIndex,ListView.Center))
        return foundIndex>=0
    }
    function transcript() {
        let text="EVA · Conversación de demostración\n\n"
        for(let i=0;i<messages.count;i++){let m=messages.get(i);text+=m.speaker+" ["+m.stamp+"]\n"+m.message+"\n\n"}
        return text
    }
    Icon{x:panel.narrow?18:26;y:20;width:panel.narrow?24:28;height:width;name:"chat"}
    Text{x:panel.narrow?54:73;y:21;text:panel.page;color:"#f0f4ff";font.pixelSize:panel.narrow?18:22;font.weight:Font.DemiBold}
    Row {x:parent.width-101;y:15;spacing:1
        IconButton{objectName:"exportButton";symbol:"download";hint:"Exportar conversación de demostración";iconSize:22;onClicked:panel.exportRequested(panel.transcript())}
        IconButton{symbol:"more";hint:"Información de la demo";iconSize:23;onClicked:panel.notice("Demostración local. Los mensajes no se envían a ningún servicio.")}
    }
    Rectangle{x:24;y:63;width:parent.width-48;height:1;color:"#34415e";opacity:.65}
    ListModel {
        id:messages
        ListElement{speaker:"TÚ";message:"¿Qué puedes hacer por mí?";stamp:"16:24";reminder:false}
        ListElement{speaker:"EVA";message:"Puedo ayudarte con información, realizar búsquedas, controlar aplicaciones como Spotify, gestionar recordatorios y mucho más.";stamp:"16:24";reminder:false}
        ListElement{speaker:"TÚ";message:"¿Puedes crear un recordatorio?";stamp:"16:25";reminder:false}
        ListElement{speaker:"EVA";message:"Por supuesto. ¿Qué recordatorio te gustaría crear?";stamp:"16:25";reminder:false}
        ListElement{speaker:"TÚ";message:"Recuérdame la reunión del proyecto mañana a las 10:00 a.m.";stamp:"16:26";reminder:false}
        ListElement{speaker:"EVA";message:"Listo. He creado un recordatorio:";stamp:"16:26";reminder:true}
    }
    ListView {
        id:chat;objectName:"conversationList"
        x:1;y:panel.compressed?72:83;width:parent.width-2;height:parent.height-y-13;clip:true
        visible:panel.page==="Conversación"
        model:messages;boundsBehavior:Flickable.StopAtBounds
        delegate:MessageBubble {
            required property int index
            required property var model
            speaker:model.speaker;message:model.message;stamp:model.stamp;reminder:model.reminder
            width:chat.width;height:implicitHeight
            highlighted:panel.foundIndex===index
        }
        ScrollBar.vertical:ScrollBar {policy:ScrollBar.AsNeeded;width:8
            contentItem:Rectangle{implicitWidth:3;radius:3;color:"#8198bb";opacity:.6}}
    }
    Item {
        objectName:"pageDetails";x:panel.compressed?16:26;y:panel.compressed?70:90;width:parent.width-2*x;height:parent.height-y-12;visible:panel.page!=="Conversación";clip:true
        Column {objectName:"pageDetailsContent";width:parent.width;spacing:panel.compressed?6:18
            Text{visible:!panel.compressed;text:panel.page;color:"#61dfff";font.pixelSize:26}
            Text{width:parent.width;text:"Vista de demostración · Sin conexión al backend";color:"#aabbd7";font.pixelSize:panel.compressed?14:17;wrapMode:Text.Wrap}
            Repeater {
                model:panel.page==="Servicios"?["Asistente de voz · Desconectado","Spotify · Sin conectar","Gemini · Sin conectar"]:
                      panel.page==="Recordatorios"?["Reunión del proyecto","Mañana a las 10:00 a.m.","Ejemplo visual · No se ha guardado"]:
                      panel.page==="Alarmas"?["07:00 · Buenos días","Alarma de ejemplo · Inactiva"]:
                      ["Tema · Holográfico azul","Calidad visual · Alta","Privacidad · Datos solo en memoria"]
                Rectangle {required property string modelData;width:parent.width;height:panel.compressed?Math.max(32,detailText.implicitHeight+12):65;radius:15;color:"#12213b";border.color:"#263d64"
                    Text{id:detailText;anchors.left:parent.left;anchors.right:parent.right;anchors.margins:panel.compressed?6:16;anchors.verticalCenter:parent.verticalCenter;text:parent.modelData;color:"#f1f2ff";font.pixelSize:panel.compressed?14:18;wrapMode:Text.Wrap}}
            }
            CheckBox {
                objectName:"reducedMotionControl";visible:panel.page==="Configuración"
                text:"Reducir movimiento";checked:panel.reducedMotion
                font.pixelSize:panel.compressed?14:18;palette.windowText:"#e3ecfa";palette.text:"#e3ecfa"
                onToggled:panel.reducedMotionRequested(checked)
            }
        }
    }
}
