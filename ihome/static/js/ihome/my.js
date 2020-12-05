function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}
function logout() {
    $.ajax({
        url:"/api/session",
        type:"delete",
        dataType:"json",
        success:function(resp) {
            if ("200" == resp.code) {
                location.href = "/index.html";
            }
        }
    })
}

$(document).ready(function(){
    $.get("/api/user-info",function(resp) {
        // 用户未登录
        if ("4101" == resp.code) {
            location.href = "/login.html";
        }
        // 查询到了用户的信息
        else if ("200" == resp.code) {
            $("#user-name").html(resp.data.name);
            $("#user-mobile").html(resp.data.mobile);
            if (resp.data.avatar_url) {
                $("#user-avatar")[0].style.display = "block"
                $("#user-avatar").attr("src", resp.data.avatar_url);
            }

        }
    }, "json")
})