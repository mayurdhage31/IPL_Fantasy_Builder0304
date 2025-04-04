document.addEventListener('DOMContentLoaded', function() {
    const matchGrid = document.getElementById('matchGrid');
    const mustIncludePlayer = document.getElementById('mustIncludePlayer');
    const riskRating = document.getElementById('riskRating');
    const teamPreference = document.getElementById('teamPreference');
    const showBestXIButton = document.getElementById('showBestXI');
    const teamDisplay = document.getElementById('teamDisplay');
    const batsmanGrid = document.getElementById('batsmanGrid');
    const wicketkeeperGrid = document.getElementById('wicketkeeperGrid');
    const allrounderGrid = document.getElementById('allrounderGrid');
    const bowlerGrid = document.getElementById('bowlerGrid');
    
    let selectedMatchIndex = null;
    let availablePlayers = [];

    // Fetch matches from the API
    fetch('/api/matches')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.matches && data.matches.length > 0) {
                data.matches.forEach((match, index) => {
                    const matchItem = document.createElement('div');
                    matchItem.className = 'match-item';
                    matchItem.textContent = match;
                    matchItem.dataset.index = index;
                    
                    matchItem.addEventListener('click', function() {
                        // Clear previous selection
                        document.querySelectorAll('.match-item').forEach(item => {
                            item.classList.remove('selected');
                        });
                        
                        // Mark as selected
                        this.classList.add('selected');
                        selectedMatchIndex = this.dataset.index;
                        
                        // Get teams from match
                        const matchText = this.textContent;
                        const teamMatch = matchText.match(/M\d+ - (.+) vs (.+)/);
                        
                        if (teamMatch && teamMatch.length === 3) {
                            const team1 = teamMatch[1];
                            const team2 = teamMatch[2];
                            
                            // Enable the player dropdown
                            mustIncludePlayer.disabled = false;
                            
                            // Clear existing options
                            mustIncludePlayer.innerHTML = '<option value="">Select players to include</option>';
                            
                            // Later, you'd fetch players for these teams and add them as options
                            // For now, let's add some placeholder options
                            const dummyPlayers = [
                                "Virat Kohli", "Rohit Sharma", "MS Dhoni", 
                                "Jasprit Bumrah", "KL Rahul", "Rishabh Pant"
                            ];
                            
                            dummyPlayers.forEach(player => {
                                const option = document.createElement('option');
                                option.value = player;
                                option.textContent = player;
                                mustIncludePlayer.appendChild(option);
                            });
                        }
                    });
                    
                    matchGrid.appendChild(matchItem);
                });
            } else {
                matchGrid.innerHTML = '<div class="match-item">No matches available</div>';
            }
        })
        .catch(error => {
            console.error('Error fetching matches:', error);
            matchGrid.innerHTML = `<div class="match-item">Error loading matches: ${error.message}</div>`;
        });

    // Event listener for the Show Best XI button
    showBestXIButton.addEventListener('click', function() {
        if (selectedMatchIndex === null) {
            alert('Please select a match first');
            return;
        }
        
        // Get selected players
        const selectedPlayers = Array.from(mustIncludePlayer.selectedOptions).map(option => option.value);
        
        // Prepare the request payload
        const payload = {
            must_include_players: selectedPlayers,
            risk_rating: riskRating.value,
            team_preference: teamPreference.value
        };
        
        // Send the request to the API
        fetch(`/api/best-xi/${selectedMatchIndex}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Clear previous team display
            batsmanGrid.innerHTML = '';
            wicketkeeperGrid.innerHTML = '';
            allrounderGrid.innerHTML = '';
            bowlerGrid.innerHTML = '';
            
            // Display the best XI
            if (data.best_xi && data.best_xi.length > 0) {
                data.best_xi.forEach(player => {
                    const playerCard = createPlayerCard(player);
                    
                    // Add to appropriate grid based on position
                    if (player.position === 'Batsman') {
                        batsmanGrid.appendChild(playerCard);
                    } else if (player.position === 'Wicketkeeper') {
                        wicketkeeperGrid.appendChild(playerCard);
                    } else if (player.position === 'All-rounder') {
                        allrounderGrid.appendChild(playerCard);
                    } else if (player.position === 'Bowler') {
                        bowlerGrid.appendChild(playerCard);
                    }
                });
                
                // Show the team display
                teamDisplay.style.display = 'block';
            } else {
                alert('No players found for this match');
            }
        })
        .catch(error => {
            console.error('Error fetching best XI:', error);
            alert(`Error: ${error.message}`);
        });
    });
    
    // Function to create a player card
    function createPlayerCard(player) {
        const card = document.createElement('div');
        card.className = 'player-card';
        
        const riskClass = player.Risk_Rating === 'High' ? 'risk-high' : 
                        player.Risk_Rating === 'Medium' ? 'risk-medium' : 'risk-low';
        
        card.innerHTML = `
            <div class="player-silhouette"></div>
            <h3 class="player-name">${player.fullName}</h3>
            <p>Team: ${player.Current_Team}</p>
            <p>Position: ${player.position}</p>
            <p class="${riskClass}">Risk: ${player.Risk_Rating}</p>
            <p>Consistency: ${parseFloat(player.Consistency).toFixed(1)}</p>
            <p>Upside: ${parseFloat(player.Upside_Potential).toFixed(1)}</p>
            <p>Total FP: ${parseFloat(player.Total_FP).toFixed(1)}</p>
        `;
        
        return card;
    }
});
