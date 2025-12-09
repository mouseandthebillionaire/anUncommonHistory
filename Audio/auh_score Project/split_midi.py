#!/usr/bin/env python3
"""
Split a MIDI file into multiple files with evenly distributed notes.
Each output file maintains original timing so they can be played together.
"""

import mido
import os

def split_midi_file(input_file, num_files=6):
    """
    Split a MIDI file into multiple files with evenly distributed notes.
    
    Args:
        input_file: Path to input MIDI file
        num_files: Number of output files to create (default: 6)
    """
    # Read the MIDI file
    print(f"Reading MIDI file: {input_file}")
    mid = mido.MidiFile(input_file)
    
    # Collect all events with absolute timing
    all_events = []
    note_on_indices = []  # Track indices of note_on events for distribution
    
    # Process all tracks
    for track in mid.tracks:
        current_time = 0
        for msg in track:
            current_time += msg.time
            all_events.append({
                'message': msg,
                'absolute_time': current_time,
                'delta_time': msg.time
            })
            
            # Track note_on events (excluding note_off sent as note_on with velocity 0)
            if msg.type == 'note_on' and msg.velocity > 0:
                note_on_indices.append(len(all_events) - 1)
    
    print(f"Found {len(note_on_indices)} note events")
    print(f"Total events: {len(all_events)}")
    
    # Distribute notes evenly across files
    # Map each note_on event to a file number
    note_to_file = {}
    for i, note_idx in enumerate(note_on_indices):
        file_num = i % num_files
        note_to_file[note_idx] = file_num
    
    # Find note_off events that correspond to each note_on
    # Track active notes: (note, channel) -> note_on_index
    active_notes = {}
    note_off_to_file = {}  # Map note_off event index to file number
    
    for i, event_data in enumerate(all_events):
        msg = event_data['message']
        
        if msg.type == 'note_on' and msg.velocity > 0:
            key = (msg.note, msg.channel)
            active_notes[key] = i
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            key = (msg.note, msg.channel)
            if key in active_notes:
                note_on_idx = active_notes[key]
                if note_on_idx in note_to_file:
                    note_off_to_file[i] = note_to_file[note_on_idx]
                del active_notes[key]
    
    # Create output files structure
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_dir = os.path.dirname(input_file) or '.'
    
    # Initialize output files - each will have a list of events with absolute times
    output_events = [[] for _ in range(num_files)]
    
    # Distribute events to appropriate files
    for i, event_data in enumerate(all_events):
        msg = event_data['message']
        
        # Determine which file(s) should receive this event
        target_files = set()
        
        if i in note_to_file:
            # This is a note_on event being distributed
            target_files.add(note_to_file[i])
        elif i in note_off_to_file:
            # This is a note_off event - goes to same file as its note_on
            target_files.add(note_off_to_file[i])
        else:
            # Non-note event (tempo, program_change, etc.) - add to all files
            target_files = set(range(num_files))
        
        # Add event to target files
        for file_num in target_files:
            output_events[file_num].append({
                'message': msg,
                'absolute_time': event_data['absolute_time']
            })
    
    # Create and write output MIDI files
    for file_num in range(num_files):
        # Create new MIDI file with same properties
        output_mid = mido.MidiFile()
        output_mid.ticks_per_beat = mid.ticks_per_beat
        output_mid.type = mid.type
        
        # Create track
        output_track = mido.MidiTrack()
        
        # Sort events by absolute time
        events = sorted(output_events[file_num], key=lambda x: x['absolute_time'])
        
        if events:
            # Build track with proper delta times
            prev_time = 0
            for event in events:
                delta = event['absolute_time'] - prev_time
                msg_copy = event['message'].copy(time=delta)
                output_track.append(msg_copy)
                prev_time = event['absolute_time']
        
        output_mid.tracks.append(output_track)
        
        # Write file
        output_filename = os.path.join(output_dir, f"{base_name}_part{file_num + 1}.mid")
        output_mid.save(output_filename)
        
        note_count = sum(1 for e in events if e['message'].type == 'note_on' and e['message'].velocity > 0)
        print(f"Created {output_filename} with {note_count} notes")
    
    print(f"\nSuccessfully created {num_files} MIDI files!")

if __name__ == '__main__':
    import sys
    
    # Default input file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_input = os.path.join(script_dir, 'piano.mid')
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = default_input
    
    if len(sys.argv) > 2:
        num_files = int(sys.argv[2])
    else:
        num_files = 6
    
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    split_midi_file(input_file, num_files)

