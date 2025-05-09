const { ipcRenderer } = require('electron');

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM fully loaded and parsed');

    document.getElementById('submit').addEventListener('click', async () => {
        const pseudo = document.getElementById('pseudo').value.trim();
        console.log('Button clicked, pseudo:', pseudo);
        if (pseudo) {
            try {
                const userInfo = await ipcRenderer.invoke('get-user-info', pseudo);
                const { image, bio, rank, points, challenges, compromissions } = userInfo;

                const imgElement = document.getElementById('user-image');
                const imgContainer = document.getElementById('user-image-container');
                const bioElement = document.getElementById('user-bio');

                if (image) {
                    imgElement.src = image;
                    imgContainer.style.display = 'flex';
                } else {
                    imgContainer.style.display = 'none';
                }

                if (bio) {
                    bioElement.innerHTML = bio;
                    bioElement.style.display = 'block';
                } else {
                    bioElement.style.display = 'none';
                }

                document.getElementById('user-rank').innerText = rank;
                document.getElementById('user-points').innerText = points;
                document.getElementById('user-challenges').innerText = challenges;
                document.getElementById('user-compromissions').innerText = compromissions;

            } catch (error) {
                console.error('Erreur lors de la récupération des informations:', error);
                document.getElementById('user-image-container').style.display = 'none';
                document.getElementById('user-bio').style.display = 'none';
            }
        } else {
            document.getElementById('user-image-container').style.display = 'none';
            document.getElementById('user-bio').style.display = 'none';
            alert('Veuillez entrer un pseudo.');
        }
    });

    ipcRenderer.on('auto-get-user-info', (event, pseudo) => {
        document.getElementById('pseudo').value = pseudo;
        document.getElementById('submit').click();
    });
});
