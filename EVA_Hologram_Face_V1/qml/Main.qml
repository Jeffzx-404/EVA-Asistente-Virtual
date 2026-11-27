import QtQuick
import QtQuick.Controls
import QtQuick.Window
import QtQuick.Dialogs
import "components"

Window {
    id:win
    objectName:"evaFaceWindow"
    title:"EVA · Hologram Face V1 · Demostración independiente"
    width:1338;height:753;minimumWidth:900;minimumHeight:600
    visible:true;color:"#030916"
    property string activePage:"Conversación"
    property string visualState:"HABLANDO"
    property bool reducedQuality:false
    property bool reducedMotion:false
    readonly property bool motionAllowed:!reducedMotion && visibility!==Window.Minimized
    // Approved compact composition: shrink to fit, never enlarge beyond 1:1.
    readonly property real designWidth:1672
    readonly property real designHeight:941
    readonly property real compositionScale:Math.min(1,viewport.width/designWidth,viewport.height/designHeight)
    property string exportText:""
    function notify(message){toastLabel.text=message;toast.open()}
    function sendMessage(){if(conversation.addMessage(composer.text)){composer.text="";activePage="Conversación";visualState="HABLANDO"}}
    onClosing:toast.close()
    Item {
        id:viewport;objectName:"pageViewport";anchors.fill:parent
        clip:true
        Background{anchors.fill:parent}
        Rectangle{anchors.fill:parent;color:"transparent";radius:20;border.color:"#3c4961";border.width:1;opacity:.7}
        Item {
            id:stage;objectName:"designStage"
            width:win.designWidth;height:win.designHeight
            scale:win.compositionScale;transformOrigin:Item.TopLeft
            x:(viewport.width-width*scale)/2;y:(viewport.height-height*scale)/2
            Item {
                id:branding;objectName:"branding";anchors.left:sidebar.left;y:14;width:410;height:72
                EvaMark{width:220;height:72;wordmark:true}
                Rectangle{x:247;y:13;width:1;height:44;color:"#a7b2cb"}
                Text{x:272;y:12;text:"Asistente\nInteligente";color:"#f1eff8";font.pixelSize:20;lineHeight:1.12}
            }
            Row{id:headerActions;anchors.right:parent.right;anchors.rightMargin:25;y:23;spacing:15
                IconButton{symbol:"bell";hint:"Notificaciones de demostración";filled:true;onClicked:win.notify("No hay notificaciones nuevas. Vista de demostración.")
                    Rectangle{x:33;y:3;width:10;height:10;radius:5;color:"#a83cff"}}
                IconButton{objectName:"settingsButton";symbol:"settings";hint:"Configuración";filled:true;onClicked:win.activePage="Configuración"}
                IconButton{symbol:"person";hint:"Perfil local de demostración";filled:true;onClicked:win.notify("Perfil EVA · Demostración local sin cuenta conectada.")}
            }
            GlassPanel {
                id:sidebar;objectName:"sidebar";anchors.left:parent.left;anchors.leftMargin:26
                y:111;width:217;height:676
                topColor:"#1b2a4b";bottomColor:"#0c2341"
                Column {id:menu;anchors.left:parent.left;anchors.right:parent.right;anchors.margins:8
                    y:44;spacing:13
                    Repeater {
                        model:[{label:"Conversación",icon:"chat"},{label:"Servicios",icon:"grid"},{label:"Recordatorios",icon:"layers"},{label:"Alarmas",icon:"bell"},{label:"Configuración",icon:"sliders"}]
                        Button {
                            id:nav;required property var modelData
                            objectName:"nav-"+modelData.label
                            width:parent.width;height:55;hoverEnabled:true;padding:0
                            Accessible.name:modelData.label
                            readonly property bool selected:win.activePage===modelData.label
                            background:Rectangle{radius:17;border.width:1;border.color:nav.activeFocus?"#99dcf3":nav.selected?"#759cce":"transparent"
                                gradient:Gradient{orientation:Gradient.Horizontal
                                    GradientStop{position:0;color:nav.selected?"#733dbb":"transparent"}
                                    GradientStop{position:.65;color:nav.selected?"#35478d":"transparent"}
                                    GradientStop{position:1;color:nav.selected?"#17658e":"transparent"}}
                                Rectangle {anchors.fill:parent;anchors.margins:1;radius:16;color:"#95bce8";opacity:nav.down?.16:nav.hovered?.08:0
                                    Behavior on opacity {enabled:win.motionAllowed;NumberAnimation{duration:120;easing.type:Easing.OutCubic}}}
                            }
                            contentItem:Item{
                                Item {anchors.centerIn:parent;width:Math.min(174,parent.width-16);height:parent.height
                                    Icon{objectName:"navIcon-"+nav.modelData.label;anchors.left:parent.left;anchors.verticalCenter:parent.verticalCenter;anchors.alignWhenCentered:false
                                        width:sidebar.width<190?24:27;height:width;name:nav.modelData.icon;ink:nav.selected?"#f1f7ff":"#c4d2e8"}
                                    Text{objectName:"navText-"+nav.modelData.label;anchors.left:parent.left;anchors.leftMargin:sidebar.width<190?34:43
                                        anchors.right:parent.right;anchors.verticalCenter:parent.verticalCenter;anchors.alignWhenCentered:false
                                        text:nav.modelData.label;color:nav.selected?"#f7f6ff":"#dce5f5";font.pixelSize:sidebar.width<190?15:18;font.weight:nav.selected?Font.Medium:Font.Normal}
                                }
                            }
                            onClicked:win.activePage=modelData.label
                        }
                    }
                }
                Rectangle{x:30;anchors.top:menu.bottom;anchors.topMargin:12;width:parent.width-60;height:1;color:"#242540"}
                Canvas {
                    x:0;y:480;width:parent.width;height:130;opacity:.65
                    onWidthChanged:requestPaint();onHeightChanged:requestPaint()
                    onPaint:{const c=getContext("2d");c.reset();const g=c.createLinearGradient(0,0,width,100);g.addColorStop(0,"#092e83");g.addColorStop(.45,"#195cff");g.addColorStop(.7,"#ac31ff");g.addColorStop(1,"#4d1694");c.strokeStyle=g
                        for(let i=0;i<28;i++){c.globalAlpha=.16;c.beginPath();c.moveTo(0,i*1.1);c.bezierCurveTo(95,25+i*3,115,130-i*2,width,50+i*3);c.stroke()}
                        c.globalAlpha=1;c.shadowBlur=14;c.shadowColor="#773eff";c.beginPath();c.moveTo(0,35);c.bezierCurveTo(120,50,110,110,width,70);c.stroke()}
                }
                Column{id:sidebarFooter;x:30;y:598;spacing:6
                    Text{text:"EVA v5.3";color:"#f1f4ff";font.pixelSize:21}
                    Text{text:"● Operativa";color:"#00ef96";font.pixelSize:19}
                }
            }
            ConversationPanel {
                id:conversation;objectName:"conversationPanel"
                anchors.left:sidebar.right;anchors.leftMargin:17;anchors.top:sidebar.top
                width:520;height:659
                page:win.activePage
                reducedMotion:win.reducedMotion
                onReducedMotionRequested:value=>win.reducedMotion=value
                onExportRequested:transcript=>{win.exportText=transcript;saveDialog.open()}
                onNotice:message=>win.notify(message)
            }
            Item {
                id:faceArea;objectName:"faceArea"
                anchors.left:conversation.right;anchors.leftMargin:10;y:54;width:490;height:692
                Item {id:portraitSlot;anchors.left:parent.left;anchors.right:parent.right;anchors.top:parent.top;height:600
                HologramStage {
                id:hologram;objectName:"hologramStage"
                anchors.centerIn:parent;width:490;height:600
                reducedQuality:win.reducedQuality
                paused:win.visibility===Window.Minimized
                }
                }
                StatusPill {id:faceStatus;objectName:"faceStatus";anchors.horizontalCenter:parent.horizontalCenter
                    anchors.bottom:parent.bottom;width:326;height:74;status:win.visualState}
            }
            MetricsPanel {
                id:metrics;objectName:"metrics"
                anchors.right:parent.right;anchors.rightMargin:25;anchors.top:sidebar.top
                width:373;height:557
                onDetailsRequested:section=>win.notify(section+": valores simulados para reproducir la referencia. No se monitoriza el equipo.")
            }
            Canvas {
                x:inputBar.x-140;y:inputBar.y-25;width:inputBar.width+280;height:150
                opacity:.55
                onWidthChanged:requestPaint()
                onPaint:{const c=getContext("2d");c.reset()
                    function light(x,y,r,color){c.save();c.translate(x,y);c.scale(1,.16);let g=c.createRadialGradient(0,0,0,0,0,r);g.addColorStop(0,color);g.addColorStop(1,"transparent");c.fillStyle=g;c.fillRect(-r,-r,2*r,2*r);c.restore()}
                    light(width*.5,98,240,"#007fc9");light(160,64,120,"#6724b8")}
            }
            GlassPanel {
                id:inputBar;objectName:"inputBar";anchors.left:conversation.left
                anchors.bottom:parent.bottom;anchors.bottomMargin:64
                width:1224;height:73;curvature:38
                topColor:"#203d65";bottomColor:"#0a213e";emphasized:composer.activeFocus
                IconButton{id:attach;x:29;anchors.verticalCenter:parent.verticalCenter;width:53;height:44;symbol:"clip";iconSize:29;hint:"Adjuntar · Vista previa";onClicked:win.notify("Los adjuntos se habilitarán en una fase posterior. No se ha abierto ningún archivo.")}
                Rectangle{id:inputDivider;anchors.left:attach.right;anchors.leftMargin:19;anchors.verticalCenter:parent.verticalCenter;width:1;height:30;color:"#556b8b"}
                TextField {
                    id:composer;objectName:"messageInput"
                    anchors.left:inputDivider.right;anchors.leftMargin:23;anchors.right:sendButton.left;anchors.rightMargin:17;anchors.verticalCenter:parent.verticalCenter;height:53
                    placeholderText:"Escribe un mensaje a EVA...";font.pixelSize:21;color:"#edf6ff";placeholderTextColor:"#afbed5"
                    selectByMouse:true;selectionColor:"#4b3790";background:Item{}
                    onAccepted:win.sendMessage()
                    Accessible.name:"Escribe un mensaje a EVA"
                }
                IconButton{id:sendButton;objectName:"sendButton";anchors.right:parent.right;anchors.rightMargin:14;anchors.verticalCenter:parent.verticalCenter;width:79;height:55;symbol:"send";iconSize:32;neon:true;filled:true;hint:"Enviar mensaje de demostración";onClicked:win.sendMessage()}
            }
            IconButton {
                id:microphone;objectName:"microphoneButton"
                anchors.left:inputBar.right;anchors.leftMargin:14;anchors.bottom:inputBar.bottom
                width:inputBar.height;height:width
                symbol:"mic";iconSize:34;filled:true;hint:"Cambiar estado visual · Sin micrófono real"
                onClicked:{win.visualState=win.visualState==="ESCUCHANDO"?"HABLANDO":"ESCUCHANDO";win.notify("Estado visual de demostración. El micrófono permanece desconectado.")}
            }
        }
    }
    FileDialog {
        id:saveDialog;title:"Exportar conversación de demostración"
        fileMode:FileDialog.SaveFile;nameFilters:["Texto (*.txt)"];defaultSuffix:"txt"
        onAccepted:win.notify(demoFiles.saveText(selectedFile,win.exportText)?"Conversación exportada.":"No se pudo guardar el archivo.")
    }
    Popup {
        id:toast;objectName:"demoToast";focus:true
        x:(win.width-width)/2;y:win.height-height-24;width:Math.min(620,win.width-50);padding:18
        closePolicy:Popup.CloseOnEscape|Popup.CloseOnPressOutside
        background:Rectangle{radius:16;color:"#eb102441";border.color:"#407da4"}
        contentItem:Text{id:toastLabel;wrapMode:Text.Wrap;font.pixelSize:16;color:"#f2f6ff";textFormat:Text.PlainText}
        onOpened:toastTimer.restart()
        Timer{id:toastTimer;interval:4200;onTriggered:toast.close()}
    }
}
