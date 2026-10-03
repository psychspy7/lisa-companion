import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import QtMultimedia

ApplicationWindow {
    id: root
    visible: false
    width: 1440; height: 900
    minimumWidth: 900; minimumHeight: 600
    title: "LISA · Kitty Corp"
    color: "#10111c"
    property bool chatVisible: true
    property int preferredChatWidth: 390
    property real zoom: lisa.initialZoom
    property string currentPortrait: lisa.portrait
    property string previousPortrait: ""
    property real dissolve: 1
    property real characterOffsetX: 0
    property real characterOffsetY: 0
    property bool ambientMotion: lisa.motionEnabled && root.visible && root.visibility !== Window.Minimized
    Component.onCompleted: root.preferredChatWidth=lisa.chatWidth
    onClosing: lisa.quit()
    Shortcut { sequence: "F11"; onActivated: root.visibility === Window.FullScreen ? root.showNormal() : root.showFullScreen() }
    Shortcut { sequence: "Escape"; onActivated: { lisa.stop(); if(root.visibility === Window.FullScreen) root.showNormal(); } }
    Shortcut { sequence: "Ctrl+H"; onActivated: root.chatVisible = !root.chatVisible }
    component SmallButton: Button {
        id: sb
        font.family: "Segoe UI"; font.pixelSize: 13
        padding: 12
        contentItem: Text { text: sb.text; color: sb.enabled ? "#e6e0f3" : "#78738a"; font: sb.font; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
        background: Rectangle { radius: 10; color: sb.down ? "#4a405e" : sb.hovered ? "#333046" : "#202131"; border.color: sb.hovered ? "#77618e" : "#363447"; border.width: 1; Behavior on color { ColorAnimation { duration: 130 } } }
    }
    Connections {
        target: lisa
        function onImageChanged(url) { if(url === root.currentPortrait) return; root.previousPortrait=root.currentPortrait; root.currentPortrait=url; root.dissolve=0; fade.restart(); }
        function onClipChanged(url) { player.stop(); player.source=url; if(url) player.play(); }
    }
    NumberAnimation { id: fade; target: root; property: "dissolve"; to: 1; duration: 360; easing.type: Easing.InOutSine; onFinished: root.previousPortrait="" }
    header: Rectangle {
        height: 78; color: "#131420"
        Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: "#2d2a3e" }
        RowLayout {
            anchors.fill: parent; anchors.leftMargin: 30; anchors.rightMargin: 24; spacing: 12
            Rectangle { width: 36; height: 36; radius: 13; color: "#b99edc"; Text { anchors.centerIn: parent; text: "☾"; font.pixelSize: 27; color: "#23182f" } }
            ColumnLayout { spacing: 2; Text { text: "LISA"; color: "#f4effa"; font.family: "Segoe UI"; font.pixelSize: 24; font.letterSpacing: 5 } Text { text: "KITTY CORP  ·  "+lisa.version; color: "#9b8cae"; font.pixelSize: 9; font.letterSpacing: 1.4 } }
            Item { Layout.fillWidth: true }
            Rectangle { visible:root.width>1040; width: modeLabel.implicitWidth+24; height: 30; radius: 15; color: "#262536"; Text { id:modeLabel; anchors.centerIn: parent; text: "●  "+lisa.modeName; color: "#c0b4d4"; font.pixelSize: 11 } }
            SmallButton { objectName:"updateButton"; text: lisa.updateInProgress ? "Updating…" : "Update"; enabled:!lisa.updateInProgress; onClicked: lisa.checkUpdate() }
            SmallButton { text: "Settings"; onClicked: lisa.settings() }
            SmallButton { text: "More  ⋯"; onClicked: appMenu.open() }
            SmallButton { text: root.visibility===Window.FullScreen ? "↙" : "⛶"; ToolTip.text: "Fullscreen · F11"; ToolTip.visible: hovered; onClicked: root.visibility===Window.FullScreen ? root.showNormal() : root.showFullScreen() }
            SmallButton { text: "×"; ToolTip.text:"Quit Lisa";ToolTip.visible:hovered;onClicked: lisa.quit() }
        }
    }
    SplitView {
        id: split
        anchors.fill: parent; anchors.margins: 16
        handle: Rectangle { implicitWidth: root.chatVisible?10:0; color: "transparent"; Rectangle { anchors.centerIn: parent; width: 3; height: 65; radius: 2; color: SplitHandle.hovered ? "#b59ad4" : "#4b405c" } }
        Item {
            id: stage
            objectName: "characterStage"
            SplitView.fillWidth: true; SplitView.minimumWidth: 430
            clip: true
            Rectangle {
                anchors.fill: parent; radius: 24
                gradient: Gradient { GradientStop { position: 0; color: "#25233c" } GradientStop { position: .6; color: "#171c32" } GradientStop { position: 1; color: "#262039" } }
                border.color: "#383347"
            }
            // Vector scenery keeps the full-screen stage crisp without a large background bitmap.
            Rectangle { x:stage.width*.07; y:45; width:stage.width*.86; height:stage.height*.73; radius: 30; color: "#18213a"; border.color: "#423850"; border.width: 2 }
            Rectangle { x:stage.width*.18; y:stage.height*.11; width:72; height:72; radius:36; color:"#ded0e6"; opacity:.65 }
            Repeater { model: 24; Rectangle { x: stage.width*(.09+((index*37)%83)/100); y: stage.height*(.08+((index*19)%42)/100); width:index%4===0?3:2; height:width; radius:width; color:"#d8c9ed"; opacity:.12+(index%5)*.07; SequentialAnimation on opacity { running: root.ambientMotion; loops: Animation.Infinite; NumberAnimation { to:.12; duration:1800+index*43 } NumberAnimation { to:.48; duration:1900+index*37 } } } }
            Repeater { model: 19; Rectangle { x:stage.width*.08+index*(stage.width*.045); y:stage.height*.63-((index*31)%75); width:stage.width*.035; height:stage.height*.13+((index*31)%75); color:index%3===0?"#2b2b48":"#25283f"; opacity:.7; Rectangle { x:5; y:12; width:4; height:3; color:"#ad8aaf"; opacity:.6 } Rectangle { x:5; y:30; width:4; height:3; color:"#bea381"; opacity:.45 } } }
            Rectangle { x:stage.width*.34; y:45; width:4; height:stage.height*.73; color:"#423950"; opacity:.6 }
            Rectangle { x:stage.width*.7; y:45; width:4; height:stage.height*.73; color:"#423950"; opacity:.6 }
            Rectangle { x:stage.width*.075; y:stage.height*.78; width:stage.width*.85; height:1; color:"#5a4b69" }
            Rectangle { x:24;y:20;width:stageLabel.implicitWidth+28;height:30;radius:15;color:"#b5202030";border.color:"#484055";Text { id:stageLabel;anchors.centerIn:parent;text:lisa.outfitName.toUpperCase()+"  /  "+lisa.moodName; color:"#c5b7d8"; font.pixelSize:10; font.letterSpacing:1.1 } }
            Text { x:28; y:59; text: "A little company. A little mischief."; color:"#92849f"; font.pixelSize:12 }
            Item {
                id: character
                anchors.horizontalCenter: parent.horizontalCenter; anchors.bottom: parent.bottom; anchors.bottomMargin:92-root.characterOffsetY
                width: parent.width; height: parent.height-110
                transform: Translate { x:root.characterOffsetX }
                scale: root.zoom
                transformOrigin: Item.Bottom
                Image { anchors.fill:parent; source:root.previousPortrait; sourceSize.width:Math.min(2160,Math.max(1024,character.height*.5625*Screen.devicePixelRatio));fillMode:Image.PreserveAspectFit; horizontalAlignment:Image.AlignHCenter; verticalAlignment:Image.AlignBottom; smooth:true; mipmap:true; asynchronous:true; opacity:1-root.dissolve }
                Image {
                    id: portraitImage
                    objectName: "portraitImage"
                    anchors.fill:parent; source:root.currentPortrait; fillMode:Image.PreserveAspectFit; horizontalAlignment:Image.AlignHCenter; verticalAlignment:Image.AlignBottom
                    sourceSize.width:Math.min(2160,Math.max(1024,character.height*.5625*Screen.devicePixelRatio))
                    smooth:true; mipmap:true; asynchronous:true; opacity:root.dissolve
                    transform: [Scale { id:breath; origin.x:portraitImage.width*.5; origin.y:portraitImage.height; xScale:1; yScale:1 }, Rotation { id:sway; origin.x:portraitImage.width*.5; origin.y:portraitImage.height; angle:0 }]
                    SequentialAnimation { running:root.ambientMotion; loops:Animation.Infinite; NumberAnimation { target:breath; property:"yScale"; to:1.005; duration:2400; easing.type:Easing.InOutSine } NumberAnimation { target:breath; property:"yScale"; to:1; duration:2500; easing.type:Easing.InOutSine } }
                    SequentialAnimation { running:root.ambientMotion; loops:Animation.Infinite; NumberAnimation { target:sway; property:"angle"; to:.2; duration:4300; easing.type:Easing.InOutSine } NumberAnimation { target:sway; property:"angle"; to:-.2; duration:4600; easing.type:Easing.InOutSine } }
                }
                MouseArea {
                    anchors.fill: parent; acceptedButtons:Qt.LeftButton
                    property real startX; property real startY; property real offsetX; property real offsetY
                    onPressed: function(mouse) { var p=mapToItem(stage,mouse.x,mouse.y);startX=p.x;startY=p.y; offsetX=root.characterOffsetX; offsetY=root.characterOffsetY }
                    onPositionChanged: function(mouse) { if(pressed){var p=mapToItem(stage,mouse.x,mouse.y); root.characterOffsetX=Math.max(-stage.width*.35,Math.min(stage.width*.35,offsetX+(p.x-startX))); root.characterOffsetY=Math.max(-100,Math.min(100,offsetY+(p.y-startY))); } }
                    onDoubleClicked: { root.characterOffsetX=0;root.characterOffsetY=0;root.zoom=1 }
                    onWheel: function(wheel) { root.zoom=Math.max(.65,Math.min(1.8,root.zoom+wheel.angleDelta.y/2400)); lisa.saveLayout(root.zoom,chatPanel.width);wheel.accepted=true }
                }
            }
            MediaPlayer { id:player; videoOutput:video; audioOutput:AudioOutput { muted:true } onErrorOccurred: player.stop() }
            VideoOutput { id:video; anchors.fill:parent; anchors.margins:20; visible:player.playbackState===MediaPlayer.PlayingState; fillMode:VideoOutput.PreserveAspectFit }
            Rectangle {
                anchors.horizontalCenter:parent.horizontalCenter; anchors.bottom:parent.bottom; anchors.bottomMargin:86; width:210; height:30; radius:15; color:"#c51c1a2b"; border.color:"#494058"
                Row { anchors.centerIn:parent; spacing:9; Repeater { model:5; Rectangle { width:3; height:lisa.talking?5+lisa.audioLevel*14+(index%3)*3:5; radius:2; color:lisa.recording?"#ddaaad":"#b59bd4"; anchors.verticalCenter:parent.verticalCenter; Behavior on height { NumberAnimation { duration:80 } } } } Text { text:lisa.recording?"Listening":lisa.talking?"Speaking":"Here with you, Sir"; color:"#c4b7d6"; font.pixelSize:10; anchors.verticalCenter:parent.verticalCenter } }
            }
            Rectangle {
                anchors.left:parent.left; anchors.right:parent.right; anchors.bottom:parent.bottom; anchors.margins:18; height:54; radius:16; color:"#d91b1b2c"; border.color:"#474055"
                RowLayout {
                    anchors.fill:parent; anchors.margins:8; spacing:7
                    SmallButton { text:"Wardrobe"; onClicked:wardrobe.open() }
                    SmallButton { text:"Expressions"; onClicked:expressions.open() }
                    Text { text:"Zoom"; color:"#b0a5c0"; font.pixelSize:11 }
                    Slider { id:zoomSlider; Layout.fillWidth:true; from:.65;to:1.8; value:root.zoom; onMoved:root.zoom=value; onPressedChanged:if(!pressed)lisa.saveLayout(root.zoom,chatPanel.width) }
                    SmallButton { objectName:"focusButton"; text:root.chatVisible?"Focus ↗":"Chat ↙"; onClicked:root.chatVisible=!root.chatVisible }
                    SmallButton { text:"↺";ToolTip.text:"Reset character position and zoom";ToolTip.visible:hovered;onClicked:{root.characterOffsetX=0;root.characterOffsetY=0;root.zoom=1;lisa.saveLayout(root.zoom,chatPanel.width)} }
                }
            }
        }
        Rectangle {
            id:chatPanel
            objectName: "chatPanel"
            visible:root.chatVisible
            SplitView.preferredWidth:root.preferredChatWidth; SplitView.minimumWidth:290; SplitView.maximumWidth:700
            radius:24; color:"#181925"; border.color:"#333042"
            onWidthChanged: layoutSave.restart()
            ColumnLayout {
                anchors.fill:parent; anchors.margins:22; spacing:18
                RowLayout { Layout.fillWidth:true; ColumnLayout { spacing:3; Text { text:"Stay a while, Sir."; color:"#eee7f5"; font.pixelSize:22; font.family:"Segoe UI" } Text { text:"YOUR CONVERSATION"; color:"#857b96"; font.pixelSize:9; font.letterSpacing:1.5 } } Item { Layout.fillWidth:true } SmallButton { text:"⋯"; onClicked:chatMenu.open() } }
                Rectangle { Layout.fillWidth:true; height:1; color:"#333041" }
                ListView {
                    id:chatList
                    Layout.fillWidth:true; Layout.fillHeight:true; clip:true; spacing:16
                    model:lisa.messages
                    ScrollBar.vertical:ScrollBar { }
                    onCountChanged:Qt.callLater(function(){chatList.positionViewAtEnd()})
                    delegate: Column {
                        required property var modelData
                        width:chatList.width; spacing:6
                        Text { text:modelData.role==="user"?"YOU":modelData.role==="assistant"?"LISA":"APP"; color:modelData.role==="user"?"#a8a4ba":"#bd9fdd"; font.pixelSize:9; font.letterSpacing:1.7 }
                        Rectangle {
                            width:parent.width; height:messageText.implicitHeight+26; radius:14; color:modelData.role==="user"?"#282539":modelData.role==="system"?"#232b31":"#20212f"; border.color:modelData.role==="assistant"?"#343044":"transparent"
                            Text { id:messageText; anchors.left:parent.left; anchors.right:parent.right; anchors.top:parent.top; anchors.margins:13; text:modelData.content; textFormat:Text.PlainText; color:modelData.role==="system"?"#afc6c4":"#e1dce9"; font.pixelSize:14; font.family:"Segoe UI"; wrapMode:Text.Wrap; lineHeight:1.2 }
                        }
                    }
                }
                Text { Layout.fillWidth:true; text:lisa.status; color:lisa.recording?"#e5acb5":"#a89ab9"; font.pixelSize:11; wrapMode:Text.Wrap }
                Rectangle {
                    Layout.fillWidth:true; height:composer.implicitHeight+22; radius:15; color:"#222231"; border.color:composer.activeFocus?"#b49acf":"#494153"; border.width:1
                    TextArea { id:composer; objectName:"composer"; anchors.fill:parent; anchors.margins:8; color:"#ede5f5"; placeholderText:"Tell me what’s on your mind…"; placeholderTextColor:"#81768f"; wrapMode:TextEdit.Wrap; font.pixelSize:14; selectByMouse:true; background:null; implicitHeight:Math.min(104,Math.max(44,contentHeight+14)); Keys.onReturnPressed:function(event){ if(!(event.modifiers & Qt.ShiftModifier)){if(!lisa.busy){lisa.send(text);text="";}event.accepted=true;} } }
                }
                RowLayout { Layout.fillWidth:true; spacing:8; SmallButton { text:lisa.recording?"■ Send voice":"● Mic"; enabled:!lisa.busy||lisa.recording; onClicked:lisa.mic() } SmallButton { text:"Stop"; onClicked:lisa.stop() } Item { Layout.fillWidth:true } SmallButton { text:"Send ↗"; enabled:!lisa.busy; onClicked:{lisa.send(composer.text);composer.text="";} } }
                Text { Layout.fillWidth:true; text:"Mic only listens while you record. Shift + Enter adds a line."; color:"#766e85"; font.pixelSize:9; wrapMode:Text.Wrap }
            }
        }
    }
    Timer { id:layoutSave; interval:600; onTriggered: if(chatPanel.width>200)lisa.saveLayout(root.zoom,chatPanel.width) }
    Rectangle {
        id:updateCard;objectName:"updateCard";visible:lisa.updateNote!=="";z:20;anchors.top:parent.top;anchors.right:parent.right;anchors.margins:26;width:Math.min(430,root.width-52);height:updateContents.implicitHeight+32;radius:16;color:"#f3222233";border.color:lisa.updateState==="error"?"#a96575":"#736084"
        ColumnLayout {
            id:updateContents;anchors.fill:parent;anchors.margins:16;spacing:12
            RowLayout { Layout.fillWidth:true;Text { text:"LISA UPDATES";color:"#d0b5ee";font.pixelSize:10;font.letterSpacing:1.5 } Item { Layout.fillWidth:true } SmallButton { visible:!lisa.updateInProgress;text:"×";padding:4;onClicked:lisa.dismissUpdate() } }
            Text { Layout.fillWidth:true;text:lisa.updateNote;wrapMode:Text.Wrap;color:"#eee7f7";font.pixelSize:13 }
            ProgressBar { Layout.fillWidth:true;visible:lisa.updateInProgress;from:0;to:1;value:Math.max(0,lisa.updateProgress);indeterminate:lisa.updateProgress<0 }
            SmallButton { visible:lisa.updateState==="error"&&!lisa.updateInProgress;text:"Try again";onClicked:lisa.checkUpdate() }
        }
    }
    Rectangle {
        visible:!root.chatVisible; anchors.horizontalCenter:parent.horizontalCenter; anchors.bottom:parent.bottom; anchors.bottomMargin:99; width:Math.min(660,parent.width-100); height:55; radius:16; color:"#ee202030"; border.color:"#595069"
        RowLayout { anchors.fill:parent; anchors.margins:8; TextField { id:focusComposer; Layout.fillWidth:true; placeholderText:"I’m listening, Sir…"; color:"#eee7f7"; font.pixelSize:14; background:null; onAccepted:{lisa.send(text);text="";} } SmallButton { text:lisa.recording?"Send voice":"Mic"; onClicked:lisa.mic() } SmallButton { text:"Stop"; onClicked:lisa.stop() } SmallButton { text:"↗"; enabled:!lisa.busy; onClicked:{lisa.send(focusComposer.text);focusComposer.text="";} } }
    }
    Popup {
        id:wardrobe; anchors.centerIn:Overlay.overlay; width:420; height:270; modal:true; padding:22; closePolicy:Popup.CloseOnEscape|Popup.CloseOnPressOutside
        background:Rectangle { radius:22; color:"#222133"; border.color:"#5b4d6d" }
        ColumnLayout { anchors.fill:parent; Text { text:"Four moods of the day"; color:"#ede4f7"; font.pixelSize:22 } Text { text:"Same Lisa. A different little vibe."; color:"#9e91af"; font.pixelSize:12 } GridLayout { columns:2; Layout.fillWidth:true; Repeater { model:["morning","afternoon","evening","night"]; SmallButton { required property string modelData; Layout.fillWidth:true; text:modelData.charAt(0).toUpperCase()+modelData.slice(1); onClicked:{lisa.setOutfit(modelData);wardrobe.close()} } } } Item { Layout.fillHeight:true } SmallButton { text:"Test voice"; onClicked:lisa.testVoice() } }
    }
    Popup {
        id:expressions; anchors.centerIn:Overlay.overlay; width:Math.min(660,root.width-60); height:Math.min(620,root.height-130); modal:true; padding:22; closePolicy:Popup.CloseOnEscape|Popup.CloseOnPressOutside
        background:Rectangle { radius:22; color:"#222133"; border.color:"#5b4d6d" }
        ColumnLayout { anchors.fill:parent; Text { text:"A face for every feeling"; color:"#ede4f7"; font.pixelSize:22 } Text { text:"36 expressions · motion clips play when saved"; color:"#a196b1"; font.pixelSize:12 } ScrollView { Layout.fillHeight:true; Layout.fillWidth:true; clip:true; GridLayout { width:parent.width; columns:4; columnSpacing:8; rowSpacing:8; Repeater { model:lisa.moods; SmallButton { required property var modelData; Layout.fillWidth:true; text:modelData.label; onClicked:{lisa.setMood(modelData.id);expressions.close()} } } } } }
    }
    Menu { id:chatMenu; MenuItem { text:"Clear conversation"; onTriggered:lisa.clearChat() } MenuItem { text:"Test voice"; onTriggered:lisa.testVoice() } MenuItem { text:"Hide chat · Ctrl+H"; onTriggered:root.chatVisible=false } }
    Menu { id:appMenu;x:root.width-width-80;y:12; MenuItem { text:"Memory";onTriggered:lisa.memory() } MenuItem { text:"Motion Studio";onTriggered:lisa.studio() } MenuSeparator {} MenuItem { objectName:"desktopShortcutOption";text:"Add desktop shortcut";onTriggered:lisa.createDesktopShortcut() } MenuItem { text:"Focus / chat · Ctrl+H";onTriggered:root.chatVisible=!root.chatVisible } MenuItem { text:"Fullscreen · F11";onTriggered:root.visibility===Window.FullScreen?root.showNormal():root.showFullScreen() } }
}
