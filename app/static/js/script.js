const socket = io();

let components = {
    guard_container: document.getElementById("guard-container"),
    guard_message: document.getElementById("guard-message"),
    video_stream: document.getElementById("video-stream"),
};

socket.on("guard", function(data) {
    let message = data.message;

    components.guard_message.style.opacity = 0;

    setTimeout(() => {
        if (message == "ok") {
            components.guard_message.innerText = "Guard is ready. No suspicious activity detected.";
        } else if (message == "alarm") {
            components.guard_message.innerText = "SUSPICIOUS ACTIVITY DETECTED. Autonomously examining the situation.";
            components.video_stream.style.outline = "4px solid dodgerblue";
        } else {
            components.guard_message.innerText = message.trim() + " Steps have been taken.";
            components.video_stream.style.outline = "4px solid #aa0000";
        }
    }, 500);

    setTimeout(() => {
        components.guard_message.style.opacity = 1;
        components.video_stream.style.outline = "none";
    }, 1000);
});
