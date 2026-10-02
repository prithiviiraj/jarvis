// Private evaluation harness. No shell, each stdin line is text only.
#include <phonemis/base/config.h>
#include <phonemis/base/pipeline.h>
#include <phonemis/utils/conversions.h>
#include <iostream>
#include <string>
int main(int argc,char**argv){
 if(argc!=4)return 2;
 phonemis::Config c;c.lang="en-us";c.phonemizer.lang=c.lang;c.phonemizer.lexicon_filepath=argv[1];c.phonemizer.nn_model_filepath=argv[2];c.tagger={.data_filepath=argv[3]};
 try {phonemis::Pipeline p(c);std::cout<<"READY"<<std::endl;std::string line;while(std::getline(std::cin,line)){
  if(line.size()>1000){std::cout<<"ERROR"<<std::endl;continue;}
  std::cout<<phonemis::utils::conversions::u32_to_utf8(p(line))<<std::endl;
 }}catch(const std::exception&){return 1;}return 0;
}
