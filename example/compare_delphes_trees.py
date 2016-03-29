import argparse
parser = argparse.ArgumentParser("FCC release set up script", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('file1', metavar='file1', type=str, help='name of file 1 to be compared with file 2')
parser.add_argument('file2', metavar='file2', type=str, help='name of file 2 to be compared with file 1')
args = parser.parse_args()

import ROOT
ROOT.gSystem.Load("libpodio")
ROOT.gSystem.Load("libdatamodel")

from ROOT import podio
from EventStore import EventStore


def compare_core(core1, core2):
    if hasattr(core1, "P4"):
        p4_1 = core1.P4
        p4_2 = core2.P4
        if not (p4_1.Px == p4_2.Px and p4_1.Py == p4_2.Py and p4_1.Pz == p4_2.Pz and p4_1.Mass == p4_2.Mass):
            print "p4 mismatch"
    if hasattr(core1, "Vertex"):
        v1 = core1.Vertex
        v2 = core2.Vertex
        if not (v1.X == v2.X and v1.Y == v2.Y and v1.Z == v2.Z):
            print "Vertex mismatch"
    for member in ["Bits", "Cellid", "Energy", "Time", "Type", "Charge", "Status", "Area"]:
        if hasattr(core1, member):
            if getattr(core1, member) != getattr(core2, member):
                print member, " mismatch"


def compare_assoc(asc1, asc2):
    for association in ["Particle", "Cluster", "Mother", "Daughter", "Rec", "Sim", "Jet"]:
        if hasattr(asc1, association):
            compare_core(getattr(asc1, association)().Core(), getattr(asc2, association)().Core())
    if hasattr(asc1, "Tag"):
        if asc1.Tag().Value() != asc2.Tag().Value():
            print "Tag mismatch"


def compare_met(met1, met2):
    for member in ["Magnitude", "Phi", "ScalarSum"]:
        if getattr(met1, member)() != getattr(met2, member)():
            print member, "mismatch"


def main():
    collnames = ["genParticles", "genVertices", "genJets", "genJetsFlavor", "muons", "muonITags", "electrons", "electronITags", "charged", "neutral", "photons", "photonITags", "jets", "jetParts", "jetsFlavor", "bTags", "cTags", "tauTags", "met", "genJetsToMC", "genJetsToFlavor", "muonsToMC", "muonsToITags", "electronsToMC", "electronsToITags", "chargedToMC", "neutralToMC", "photonsToMC", "photonsToITags", "jetsToParts", "jetsToFlavor", "jetsToBTags", "jetsToCTags", "jetsToTauTags"]

    wrong_per_cat = {}
    for name in collnames:
        wrong_per_cat[name] = 0

    fnew = EventStore([args.file1])
    fold = EventStore([args.file2])

    nevents = len(fnew)
    imismatch = 0
    nvalues_examined = 0
    for iev in range(nevents):
        ev_new = fnew[iev]
        ev_old = fold[iev]
        for collname in collnames:
            coll_old = ev_old.get(collname)
            coll_new = ev_new.get(collname)
            if isinstance(coll_old, podio.CollectionBase):
                if coll_old.size() != coll_new.size():
                    imismatch += 1
                    print collname, coll_old.size(), coll_new.size()
                    wrong_per_cat[collname] += 1
                for i in range(coll_old.size()):
                    nvalues_examined += 1
                    item_old = coll_old.at(i)
                    item_new = coll_new.at(i)
                    if hasattr(item_old, "Core"):  # Compare particles + jets
                        compare_core(item_old.Core(), item_new.Core())
                    elif hasattr(item_old, "Value"):  # Compare Tags
                        if item_old.Value() != item_new.Value():
                            print "Value mismatch"
                    elif hasattr(item_old, "Position"):  # Compare Vertices
                        p_old, p_new = item_old.Position(), item_new.Position()
                        if not (p_old.X == p_new.X and p_old.Y == p_new.Y and p_old.Z == p_new.Z):
                            print "Position mismatch"
                    elif "Association" in item_old.__repr__():  # Compare associations
                        compare_assoc(item_old, item_new)
                    else:  # only met should be left
                        compare_met(item_old, item_new)

    print imismatch, "/", nvalues_examined, "have mismatches, per category:"
    print wrong_per_cat


if __name__ == "__main__":
    main()
