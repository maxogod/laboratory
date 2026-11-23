#ifndef TALLER_SERIALIZER_H
#define TALLER_SERIALIZER_H

#include <string>
#include <unordered_map>
#include <vector>

#define SPACE " "
#define NOP 0x00

class Serializer {
private:
    static const std::unordered_map<std::string, uint8_t> action_string_to_code;
    static const std::unordered_map<uint8_t, std::string> action_code_to_string;

public:
    static std::vector<uint8_t> serialize(const std::string& request);
    static std::string deserialize(const std::vector<uint8_t>& request);
};


#endif  // TALLER_SERIALIZER_H
