/* Add your custom JavaScript code here */

let modal_file_viewer ; 
let should_prevent_htmx = true;

function removeActiveDirectoryClass() {
    // Select all elements with the class 'active_directory'
    const elements = document.querySelectorAll('.active_directory');
    
    // Loop through the NodeList of elements and remove the class
    elements.forEach(function(element) {
        element.classList.remove('active_directory');
    });
}

function toggleFolder(element, event) {
    let parent = element.parentElement;
    removeActiveDirectoryClass();
    element.classList.add('active_directory');
    document.getElementById('current_active_dir').value = element.getAttribute('data-ffe-dir');
    var cur_dir = element.getAttribute('data-ffe-dir');
    if (! cur_dir.startsWith('/')) {
        cur_dir = '/' + cur_dir;
    }
    document.getElementById('current_directory_name').innerHTML = cur_dir;
    sublisting = parent.querySelector('ul'); // .directory-listing
    
    if (sublisting.classList.contains('directory-list')) {
        
        if (sublisting.style.display == 'none') {
            sublisting.style.display = 'block';
            
        } else {
            sublisting.style.display = 'none';
        }
        //sublisting.classList.toggle('d-none');
        //ul = document.createElement('ul');
        //parent.appendChild(ul);
        if (should_prevent_htmx) {
            event.preventDefault();
            element.dispatchEvent(new Event('htmx:abort'));
        } else {
            sublisting = document.createElement('ul');
            should_prevent_htmx = true;
        }
    }
}

document.body.addEventListener('htmx:afterSwap', function(evt) {
    
    if (evt.detail.target.id === 'file-viewer') {
        var file_name = evt.detail.requestConfig.elt.getAttribute('data-ffe-file');
        if (! file_name.startsWith('/')) {
            file_name = '/' + file_name;
        }
        document.getElementById('ffe-modal-title').innerHTML = file_name;
        
        var myModal = new bootstrap.Modal(document.getElementById('modal-file-viewer'), {
            keyboard: true ,    // To dismiss modal with escape key
            autoProcessQueue: false
        });
        
        myModal.show();
    }
});


Dropzone.options.ffeUploadForm = {
    init: function() {
        this.on('success', function(file) {
            console.log("Uploaded file:");
            console.log(file);
            full_name = $("#current_active_dir").val()
            console.log(full_name);
            should_prevent_htmx = false;
            
            $("a.active_directory")[0].click();

        });
    }
}
