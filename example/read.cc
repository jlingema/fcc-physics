#include "datamodel/MCParticleCollection.h"
#include "datamodel/EventInfoCollection.h"
#include "datamodel/JetCollection.h"
#include "datamodel/JetParticleAssociationCollection.h"

// Utility functions
#include "utilities/JetUtils.h"
#include "utilities/VectorUtils.h"
#include "utilities/ParticleUtils.h"
#include "utilities/GraphBuilder.h"

// ROOT
#include "TBranch.h"
#include "TFile.h"
#include "TTree.h"
#include "TROOT.h"
#include "TLorentzVector.h"

// STL
#include <vector>
#include <iostream>

// podio specific includes
#include "podio/EventStore.h"
#include "podio/ROOTReader.h"

std::ostream& operator<<(std::ostream& out, const fcc::MCParticle& ptc) {
  if(not out) return out;
  const fcc::BareParticle& pcore = ptc.Core();
  TLorentzVector p4 = utils::lvFromPOD(pcore.P4);
  out<< "particle ID " << pcore.Type
     << " e " << p4.E()
     << " pt " << p4.Pt()
     << " eta " << p4.Eta()
     << " phi " << p4.Phi();
  return out;
}

void processEvent(podio::EventStore& store,
                  bool verbose,
                  podio::ROOTReader& reader,
                  fcc::GraphBuilder& graph) {

  // read event information
  const fcc::EventInfoCollection* evinfocoll(nullptr);
  bool evinfo_available = store.get("EventInfo", evinfocoll);
  if(evinfo_available) {
    auto evinfo = evinfocoll->at(0);

    if(verbose)
      std::cout << "event number " << evinfo.Number() << std::endl;
  }

  // read particles
  const fcc::MCParticleCollection* ptcs(nullptr);
  bool particles_available = store.get("GenParticle", ptcs);
  if (particles_available){
    graph.build(*ptcs);
    DAG::BFSVisitor<fcc::IdNode> visitor;
    std::vector<fcc::MCParticle> muons;
    std::vector<fcc::MCParticle> higgses;
    // there is probably a smarter way to get a vector from collection?

    if(verbose)
      std::cout << "particle collection:" << std::endl;
    for(const auto& ptc : *ptcs){
      if(verbose)
        std::cout<<"\t"<<ptc<<std::endl;
      if( ptc.Core().Type == 4 ) {
        muons.push_back(ptc);
      } else if (ptc.Core().Type == 25) {
        higgses.push_back(ptc);
      }
    }
    for (const auto& higgs : higgses) {
      const fcc::IdNode& higgsNode = graph.getNode(higgs);
      if (verbose) {
        std::cout << higgs << std::endl;
        std::cout << "decayproducts;" << higgsNode.children().size() << std::endl;
        std::cout << "     decay products: ";
      }
      for (auto n : visitor.traverseChildren(higgsNode)) {
        // not needed because we are working with only one collection:
        // const fcc::MCParticleCollection* ptcs(nullptr);
        // bool particles_available = store.get(n->value.collectionID, ptcs);
        const auto& topDaughter = ptcs->at(n->value().index);
        if (verbose) {
          std::cout << topDaughter << ", ";
        }
      }
      if (verbose) {
        std::cout << std::endl;
      }
    }
  }
}

int main(int argc, char** argv){
  auto reader = podio::ROOTReader();
  auto store = podio::EventStore();
  auto graph = fcc::GraphBuilder();
  if( argc != 2) {
    std::cerr<<"Usage: pythiafcc-read filename"<<std::endl;
    return 1;
  }
  const char* fname = argv[1];
  try {
    reader.openFile(fname);
  }
  catch(std::runtime_error& err) {
    std::cerr<<err.what()<<". Quitting."<<std::endl;
    exit(1);
  }
  store.setReader(&reader);

  bool verbose = true;

  // unsigned nEvents = 5;
  unsigned nEvents = reader.getEntries();
  for(unsigned i=0; i<nEvents; ++i) {
    if(i%1000==0) {
      std::cout<<"reading event "<<i<<std::endl;
    }
    if(i>10) {
      verbose = false;
    }
    processEvent(store, verbose, reader, graph);
    graph.clear();
    store.clear();
    reader.endOfEvent();
  }
  return 0;
}
