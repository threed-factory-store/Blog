window.addEventListener('DOMContentLoaded', function() {
    homeLink = document.getElementById("homeLink")
    header = document.getElementById("header")
    content = document.getElementById("content")

    visualViewport.addEventListener("resize", () => {
        var style = window.getComputedStyle(homeLink).getPropertyValue('font-size');
        var fontSize = parseFloat(style); 
        // now you have a proper float for the font size (yes, it can be a float, not just an integer)
        header.style.height = fontSize+"px"
        content.style.marginTop = fontSize+"px"
    })
})
