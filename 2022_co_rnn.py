# -*- coding: utf-8 -*-
"""2022_co-rnn.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1fi8atR0zvb2vkj4Eg0omZmBd7E_ThIEy
"""

import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# Define the coRNNCell
class coRNNCell(nn.Module):
    def __init__(self, n_inp, n_hid, dt, gamma, epsilon):
        super(coRNNCell, self).__init__()
        self.dt = dt
        self.gamma = gamma
        self.epsilon = epsilon
        self.i2h = nn.Linear(n_inp + n_hid + n_hid, n_hid)

    def forward(self, x, hy, hz):
        hz = hz + self.dt * (torch.tanh(self.i2h(torch.cat((x, hz, hy), 1)))
                             - self.gamma * hy - self.epsilon * hz)
        hy = hy + self.dt * hz
        return hy, hz

# Define the coRNN model
class coRNN(nn.Module):
    def __init__(self, n_inp, n_hid, n_out, dt, gamma, epsilon):
        super(coRNN, self).__init__()
        self.n_hid = n_hid
        self.cell = coRNNCell(n_inp, n_hid, dt, gamma, epsilon)
        self.readout = nn.Linear(n_hid, n_out)

    def forward(self, x):
        hy = torch.zeros(x.size(1), self.n_hid)
        hz = torch.zeros(x.size(1), self.n_hid)

        for t in range(x.size(0)):
            hy, hz = self.cell(x[t], hy, hz)
        output = self.readout(hy)
        return output

# Set random seed for reproducibility
torch.manual_seed(42)

# Toy problem data
input_size = 1
hidden_size = 32
output_size = 1
sequence_length = 52
batch_size = 1
num_epochs = 10000



# Load data from CSV file
data_path = "/content/csv_export (3).csv"
data = pd.read_csv(data_path, delimiter=';')

input_column = data['2022']
input_column_str = input_column.astype(str)
input_column_numeric = pd.to_numeric(input_column_str.str.replace(',', '.'), errors='coerce')
# Drop any rows with missing values
data_numeric = pd.DataFrame({
   'input_column': input_column_numeric,
})

data_path = "/content/csv_export (4).csv"
data = pd.read_csv(data_path, delimiter=';')

# Extract data from the second and third columns
output_column = data['2022']  # Replace '2018-2021' with the actual column name
# Convert data to strings
output_column_str = output_column.astype(str)
# Convert strings to numeric values
output_column_numeric = pd.to_numeric(output_column_str.str.replace(',', '.'), errors='coerce')
# Drop any rows with missing values
data_numeric = pd.DataFrame({
    'output_column': output_column_numeric,
})
def min_max_scaling(data):
    min_val = np.min(data)
    max_val = np.max(data)
    scaled_data = (data - min_val) / (max_val - min_val)
    return scaled_data


# Example usage:
input_scaled_data = min_max_scaling(input_column_numeric)
output_scaled_data = min_max_scaling(output_column_numeric)


# Convert data to tensors
input_tensor = torch.tensor(input_scaled_data).view(batch_size, sequence_length, input_size).float()
target_tensor = torch.tensor(output_scaled_data).view(batch_size, sequence_length, output_size).float()


# Select even indices for both input and output(train)
input_tensor_train = input_tensor[:, 1::2, :]
target_tensor_train = target_tensor[:,1::2, :]

#testing
input_tensor_testing = input_tensor[:, ::2, :]
target_tensor_testing = target_tensor[:, ::2, :]

print(input_tensor_train.shape)
print(target_tensor_train.shape)

print(input_tensor_testing.shape)
print(target_tensor_testing.shape)



# Create coRNN instance
cornn = coRNN(input_size, hidden_size, output_size, dt=0.1, gamma=1.0, epsilon=0.01)


# Loss and optimizer
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(cornn.parameters(), lr=0.01)

# Training loop
for epoch in range(num_epochs):
    # Forward pass
    output = cornn(input_tensor)
    loss = criterion(output, target_tensor)

    # Backward and optimize
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    # Print progress
    if (epoch + 1) % 10 == 0:
        print(f'Epoch: {epoch + 1}/{num_epochs}, Loss: {loss.item():.4f}')

# Convert data to tensor for prediction
input_tensor_pred = input_tensor_testing
with torch.no_grad():
    prediction = cornn(input_tensor_pred)
    ground_truth = target_tensor_testing

# Convert the PyTorch tensors to NumPy arrays
prediction = prediction.numpy()
ground_truth = ground_truth.numpy()

# Compute the relative L2 error norm (generalization error)
relative_error_test = np.mean((prediction - ground_truth)**2) / np.mean(ground_truth**2)
print("Relative Error Test: ", relative_error_test * 100)


# # Choose a specific sequence for plotting (e.g., the first sequence in the batch)
#  sequence_index = 0

# # Flatten the tensors for plotting
# input_data = input_tensor_testing[sequence_index, :, 0].flatten().numpy()
# ground_truth_data = target_tensor_testing[sequence_index, :, 0].flatten().numpy()
# prediction_data = prediction[0, :, 0].flatten()

# # # Plot input tensor testing against target tensor testing
# # plt.figure(figsize=(12, 6))
# # plt.plot(input_tensor_testing[sequence_index, :, 0], target_tensor_testing[sequence_index, :, 0], label='Ground Truth (Testing)', marker='o', linestyle='None')
# # plt.plot(input_tensor_testing[sequence_index, :, 0], prediction[:, 0], label='Model Prediction', marker='o', linestyle='None')

# # plt.title('Input Tensor Testing vs Prediction')
# # plt.xlabel('Input Tensor (Testing)')
# # plt.ylabel('Prediction')
# # plt.legend()
# # plt.show()

sequence_index = 0

def reverse_min_max_scaling(scaled_data, original_min, original_max):
    original_data = scaled_data * (original_max - original_min) + original_min
    return original_data


# Save the min and max values for later use
original_min = np.min(output_column_numeric)
original_max = np.max(output_column_numeric)

# Reverse the scaling to obtain the original data
prediction_data = reverse_min_max_scaling(prediction[:, 0], original_min, original_max)
ground_truth_data = reverse_min_max_scaling(target_tensor_testing[sequence_index, :, 0], original_min, original_max)


# Plotting
plt.grid(False)  # Turn off the grid

weeks = np.linspace(1,52,26)
print(weeks.shape)
print(prediction_data.shape)

# Plot the ground truth in red and the network prediction in dark blue with thicker lines
plt.plot(weeks,prediction_data, lw=4, color='red')


plt.plot(weeks, ground_truth_data, lw=4, color='black')

# Set x and y labels, legend font size, and legend font weight
plt.xlabel("Weeks", fontsize=15, fontweight='normal')
plt.ylabel("GWh/day", fontsize=15, fontweight='normal')

# Increase the size of axis ticks
# plt.tick_params(axis='both', which='both', labelsize=25)  # Adjust the labelsize as needed
plt.tick_params(axis='both')


# Save the figure in PDF format with DPI 300 and tight layout
plt.savefig("2022_CO-RNN.jpeg", dpi=300, bbox_inches='tight')
plt.show()

# Plotting
plt.grid(False)  # Turn off the grid

# Plot the ground truth in red and the network prediction in dark blue with thicker lines
plt.plot(input_column_numeric, lw=4, color='blue')



# Set x and y labels, legend font size, and legend font weight
plt.xlabel("Weeks", fontsize=15, fontweight='normal')
plt.ylabel("Temperature (°C)", fontsize=15, fontweight='normal')

# Increase the size of axis ticks
# plt.tick_params(axis='both', which='both', labelsize=25)  # Adjust the labelsize as needed
plt.tick_params(axis='both')


# Save the figure in PDF format with DPI 300 and tight layout
plt.savefig("2022_co-rnn_input.jpeg", dpi=300, bbox_inches='tight')
plt.show()

