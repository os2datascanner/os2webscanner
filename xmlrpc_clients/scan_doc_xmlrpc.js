/**
 * Created by danni on 9/27/17.
 */
/**
 * Function to scan a file using OS2Webscanner xmlrpc interface.
 * Is dependent on jQuery xmlrpc lib. https://plugins.jquery.com/xmlrpc/
 */
function scanFile() {
    var username = prompt("Indtast dit OS2Webscanner brugernavn", "");
    var password = prompt("Indtast dit OS2Webscanner kodeord", "");
    var file = document.getElementById('filetoscan').files[0];
    if (file) {
        // create reader
        var reader = new FileReader();
        reader.readAsText(file, 'utf-8');
        reader.onload = function(e) {
            binarydata = e.target.result
            encodeddata = binarydata.replace(/[æøåÆØÅ]/g, '')
            $.xmlrpc({
                url: 'https://webscanner.magenta-aps.dk/xmlrpc/',
                methodName: 'scan_documents',
                params: [username, password, [[encodeddata, file.name]], { 'do_cpr_scan': 'True' }],
                success: function(response, status, jqXHR) {
                    alert('Rapporten kan findes her: ' + response[0])
                },
                error: function(jqXHR, status, error) {
                    alert('Der skete en fejl under scanningen.')
                }
            });
        };
    }
}