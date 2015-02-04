#!/usr/bin/env python3

import sys, argparse
import matplotlib.pyplot as plt
from multiprocessing import Pool

from fourmomentum import FourMomentum
from event import Event


#Number filter (more than n events)
def number_threshold(events, n):
    """ Filters events so that only events with more than
        n momenta are returned. """
    return list(filter(lambda x: len(x) > n, events))

#Transverse  momentum filter
def transverse_threshold(events, p_T):
    for event in events:
        event.momenta = list(filter(lambda x: x.transverse() > p_T, event.momenta))
    return events

#Keeps the 20GeV transverse momentum
def transverse_threshold_2(events, p_T):
    events2 = []
    for event in events:
        for momenta in event.momenta:
            if momenta.transverse() > p_T:
                events2.append(event)
    return events2

#Energy filter
def energy_threshold(events, E):
    for event in events:
        event.momenta = list(filter(lambda x: x.energy > E, event.momenta))
    return events

#combined filter
def combined_filter(events):
     #Filtering events
    res = energy_threshold(events, 40)

    #One photon with transverse momentum > 20GeV
    res = transverse_threshold(res, 20)

    #The other photon with p_T >40GeV
    res = transverse_threshold_2(res, 40)

    #only show events with at least 2 momenta
    res = number_threshold(res, 1)

    for event in res:
        event.filter_highest(2)
        #event.filter_2_angles()

    for event in res:
        if len(event) > 2:
            raise ValueError
    return res

def get_invariant_masses(events):
    invariant_masses = []
    for i, event in enumerate(events):
        invariant_masses.append(event.invariant_mass())
    return invariant_masses

def parse_file(path, count=False, momenta_in_event=False):
    """ Parse the event file with name path returning Event objects.

        Keyword arguments:
        path  -- The filepath of the event file
        count -- Whether to print the current num. processed events
        momenta_in_event -- Whether to use file containing num. four
                            momenta in each event.

        The four momenta count file should have the filename path + '_count'
        and each line should contain the number of four momenta in each
        event of the events file (as specified in the path argument) in
        order of event appearance (the first number in the count file
        has the number of four momenta in the first event of the events file)."""

    events = []
    with open(path) as data_file:
        raw = data_file.read().split('\n')

        if momenta_in_event:
            count_file = open(path + '_count')
            counts = count_file.read().split('\n')
            # Current event number in file
            current_event_number = 0

        four_momenta_count = 0
        counter = 0
        p = Pool(100)
        for i, line in enumerate(raw):
            # If the line starts with 'Event', begin to process it
            if line.startswith('Event'):
                # If number of momenta given, use that, else just use 20
                if momenta_in_event:
                    four_momenta_count = int(counts[current_event_number])
                    current_event_number += 1
                else:
                    four_momenta_count = 20

                new_event = Event.from_text(raw[i+1:i+four_momenta_count])
                p.apply_async(events.append(new_event))
                #events.append(Event.from_text(raw[i:i+10]))

                if count:
                    counter += 1
                    if counter % 1000 == 0:
                        print(counter)



    return events


def main():
    parser = argparse.ArgumentParser(description='Generate histogram from Higgs event data')
    parser.add_argument('--higgs', nargs=1, default='higgs.txt', metavar='path_to_higgs',
                        dest='higgs_path', help='Relative path to higgs data')
    parser.add_argument('--background', nargs=1, default='background.txt', metavar='path_to_background',
                        dest='background_path', help='Relative path to background data')
    parser.add_argument('--print_higgs', action='store_true',
                        help='Whether to print the calculated invariant masses of the Higgs signal to stdout.')
    parser.add_argument('--print_bkg', action = 'store_true',
                        help='Whether to print the calculated invariant masses of the background to stdout.')
    parser.add_argument('--parsed_higgs', action='store_true',
                        help='Print parsing information of Higgs signal to stdout.')
    parser.add_argument('--parsed_bkg', action='store_true',
                        help='Print parsing information of background to stdout.')
    parser.add_argument('--count', action='store_true',
                        help='Whether to print current line of parsing.')
    parser.add_argument('--momenta_count_in_event', action='store_false',
        help="""Use files which hold the number of events in the event,
                with the name of the datafile + '_count'.""")

    args = parser.parse_args()

    # Higgs signal
    higgs_events = parse_file(args.higgs_path, count=args.count,
            momenta_in_event=args.momenta_count_in_event)
    higgs_events = combined_filter(higgs_events)
    invariant_masses_higgs = get_invariant_masses(higgs_events)
    #Comment out the background if you want to change functions etc.
    # Background (comment out all 3 lines to do quick work)
    bkg_events = parse_file(args.background_path, count=args.count,
            momenta_in_event=args.momenta_count_in_event)
    bkg_events = combined_filter(bkg_events)
    invariant_masses_bkg = get_invariant_masses(bkg_events)
    # Much more clear filtering by using a function
    invariant_masses_combined = invariant_masses_higgs + invariant_masses_bkg

    if args.print_higgs:
        for mass in invariant_masses_higgs:
            print(mass)

    if args.print_bkg:
        for mass in invariant_masses_bkg:
            print(mass)

    if args.parsed_higgs:
        for event in higgs_events:
            print(event.momenta)
            print('Event', event.id)
            for momenta in event.momenta:
                print('Energy:', momenta.energy)
                print('p_T:', momenta.transverse())

            print('Invariant mass:', invariant_mass)

    if args.parsed_bkg:
        for event in bkg_events:
            print(event.momenta)
            print('Event', event.id)
            for momenta in event.momenta:
                print('Energy:', momenta.energy)
                print('p_T:', momenta.transverse())

            print('Invariant mass:', invariant_mass)

    out_higgs = open('outputIM_Higgs.txt', 'w')
    out_bkg = open('outputIM_bkg.txt', 'w')
    out_comb = open('outputIM_cmb.txt', 'w')
    out_higgs.write(str(invariant_masses_higgs))
    out_bkg.write(str(invariant_masses_bkg))
    out_comb.write(str(invariant_masses_combined))


if __name__ == '__main__':
    main()


