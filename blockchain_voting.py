import tkinter as tk
from tkinter import ttk, messagebox, StringVar
import hashlib
import json
from time import time
from uuid import uuid4
import requests

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_votes = []
        self.nodes = set()
        self.registered_voters = set()  # Store registered voters separately

        # Create the genesis block
        self.new_block(previous_hash='1', proof=100)

    def register_node(self, address):
        # Add a new node to the list of nodes
        self.nodes.add(address)

    def new_block(self, proof, previous_hash=None):
        # Create a new block in the blockchain
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'votes': self.current_votes.copy(),
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]) if self.chain else None,
        }

        # Add the block to the chain
        self.chain.append(block)

        # Reset the current list of votes
        self.current_votes = []

        return block

    def new_vote(self, voter_id, candidate):
        # Check if the voter is registered
        if voter_id not in self.registered_voters:
            return False  # Voter not registered

        # Check if the voter already voted
        for block in self.chain:
            for vote in block['votes']:
                if vote['voter_id'] == voter_id:
                    return False  # Voter already voted

        # Create a new vote and add it to the list of votes
        self.current_votes.append({
            'voter_id': voter_id,
            'candidate': candidate,
        })

        return True

    def register_voter(self, voter_id):
        # Register a new voter
        if voter_id in self.registered_voters:
            return False  # Voter already registered

        self.registered_voters.add(voter_id)  # Update the set of registered voters immediately
        return True

    def hash(self, block):
        # Hash a block
        return hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()

    def proof_of_work(self, last_proof):
        # Simple proof-of-work algorithm
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        # Validate the proof: Does hash(last_proof, proof) contain 4 leading zeroes?
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


class BlockchainGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Blockchain Voting System")

        self.candidates_frame = ttk.LabelFrame(root, text="Candidates and Voting Percentage")
        self.candidates_frame.grid(row=0, column=0, padx=10, pady=10)

        self.voting_frame = ttk.LabelFrame(root, text="Vote for a Candidate")
        self.voting_frame.grid(row=1, column=0, padx=10, pady=10)

        self.chart_frame = ttk.LabelFrame(root, text="Voting Chart")
        self.chart_frame.grid(row=2, column=0, padx=10, pady=10)

        self.status_frame = ttk.LabelFrame(root, text="Network Status")
        self.status_frame.grid(row=3, column=0, padx=10, pady=10)

        self.registration_frame = ttk.LabelFrame(root, text="Voter Registration")
        self.registration_frame.grid(row=4, column=0, padx=10, pady=10)

        self.candidates_label = tk.Label(self.candidates_frame, text="Candidates:")
        self.candidates_label.pack()

        self.votes_label = tk.Label(self.candidates_frame, text="Voting Percentage:")
        self.votes_label.pack()

        self.voter_id_label = tk.Label(self.voting_frame, text="Enter Social Security Number:")
        self.voter_id_entry = tk.Entry(self.voting_frame)
        self.voter_id_label.grid(row=0, column=0, padx=5, pady=5)
        self.voter_id_entry.grid(row=0, column=1, padx=5, pady=5)

        self.candidate_label = tk.Label(self.voting_frame, text="Select Candidate:")
        self.candidate_var = StringVar()
        self.candidate_var.set("Candidate A")  # Default candidate
        candidates = ["Candidate A", "Candidate B", "Candidate C"]  # Add more candidates as needed
        self.candidate_menu = ttk.Combobox(self.voting_frame, textvariable=self.candidate_var, values=candidates)
        self.candidate_menu.grid(row=1, column=1, padx=5, pady=5)
        self.candidate_label.grid(row=1, column=0, padx=5, pady=5)

        self.vote_button = tk.Button(self.voting_frame, text="Vote", command=self.cast_vote)
        self.vote_button.grid(row=2, column=0, columnspan=2, pady=10)

        self.chart_canvas = tk.Canvas(self.chart_frame, width=400, height=300)
        self.chart_canvas.pack()

        self.status_text = tk.Text(self.status_frame, width=60, height=10, wrap=tk.WORD)
        self.status_text.pack()

        self.registration_label = tk.Label(self.registration_frame, text="Register Voter (Enter SSN):")
        self.registration_entry = tk.Entry(self.registration_frame)
        self.registration_label.grid(row=0, column=0, padx=5, pady=5)
        self.registration_entry.grid(row=0, column=1, padx=5, pady=5)

        self.register_button = tk.Button(self.registration_frame, text="Register Voter", command=self.register_voter)
        self.register_button.grid(row=1, column=0, columnspan=2, pady=10)

        # Generate a globally unique address for this node
        self.node_identifier = str(uuid4())

        self.update_gui()

    def update_gui(self):
        # Update candidates and voting percentage
        candidates, percentages = self.calculate_voting_percentage()
        candidates_str = "\n".join(f"{c}: {p}%" for c, p in zip(candidates, percentages))
        self.candidates_label.config(text=f"Candidates:\n{candidates_str}")
        self.votes_label.config(text=f"Voting Percentage:\n{candidates_str}")

        # Update chart
        self.update_chart(candidates, percentages)

        # Update network status
        network_status = self.get_network_status()
        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(tk.END, network_status)

        # Schedule the update after 5000 milliseconds (5 seconds)
        self.root.after(5000, self.update_gui)

    def calculate_voting_percentage(self):
        total_votes = len(blockchain.current_votes)
        candidates = set(vote['candidate'] for block in blockchain.chain for vote in block['votes'])
        percentages = [0] * len(candidates)

        for i, candidate in enumerate(candidates):
            candidate_votes = sum(1 for block in blockchain.chain for vote in block['votes'] if
                                  vote['candidate'] == candidate)
            percentages[i] = (candidate_votes / total_votes) * 100 if total_votes > 0 else 0

        return candidates, percentages

    def update_chart(self, candidates, percentages):
        self.chart_canvas.delete("all")

        if not candidates or not percentages:
            return

        colors = ['blue', 'green', 'red', 'purple', 'orange']
        total_percentage = sum(percentages)

        start_angle = 0
        for i, (candidate, percentage) in enumerate(zip(candidates, percentages)):
            angle = (percentage / total_percentage) * 360
            self.chart_canvas.create_arc(50, 50, 250, 250, start=start_angle, extent=angle, fill=colors[i],
                                        outline="white")
            start_angle += angle

        self.chart_canvas.create_text(150, 150, text="Voting Chart", font=("Helvetica", 16), fill="black")

    def get_network_status(self):
        status = f"Node ID: {self.node_identifier}\n"
        status += f"Current Chain Length: {len(blockchain.chain)}\n"
        status += f"Current Votes: {len(blockchain.current_votes)}\n"
        status += f"Registered Voters: {len(blockchain.registered_voters)}\n"  # Display the number of registered voters
        status += f"Registered Nodes: {len(blockchain.nodes)}\n"

        return status

    def cast_vote(self):
        voter_id = self.voter_id_entry.get()
        if not voter_id:
            messagebox.showerror("Error", "Please enter your Social Security Number.")
            return

        # Check for voter eligibility (simple registration check for demonstration)
        if not blockchain.registered_voters:
            messagebox.showerror("Error", "No registered voters. Please register first.")
            return

        candidate = self.candidate_var.get()

        # Attempt to cast the vote
        if blockchain.new_vote(voter_id, candidate):
            messagebox.showinfo("Success", "Vote successfully cast.")
        else:
            messagebox.showerror("Error", "You have already voted or an error occurred.")

        # Clear the voter ID entry
        self.voter_id_entry.delete(0, tk.END)

    def register_voter(self):
        voter_id = self.registration_entry.get()
        if not voter_id:
            messagebox.showerror("Error", "Please enter a Social Security Number.")
            return

        # Attempt to register the voter
        if blockchain.register_voter(voter_id):
            messagebox.showinfo("Success", "Voter successfully registered.")
        else:
            messagebox.showerror("Error", "Voter already registered or an error occurred.")

        # Clear the registration entry
        self.registration_entry.delete(0, tk.END)

# Run the GUI
app = tk.Tk()
blockchain = Blockchain()
gui = BlockchainGUI(app)
app.after(0, gui.update_gui)  # Start the update mechanism immediately
app.mainloop()
