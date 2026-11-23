#include "Serializer.h"

#include <sstream>

const std::unordered_map<std::string, uint8_t> Serializer::action_string_to_code = {
        {"JUMP", 0x01}, {"RIGHT", 0x02}, {"LEFT", 0x03}, {"DUCK", 0x04}, {"HIT", 0x05},
};

const std::unordered_map<uint8_t, std::string> Serializer::action_code_to_string = {
        {0x01, "JUMP"}, {0x02, "RIGHT"}, {0x03, "LEFT"}, {0x04, "DUCK"}, {0x05, "HIT"},
};

// Serialization methods
std::vector<uint8_t> Serializer::serialize(const std::string& request) {
    std::vector<uint8_t> serialized;
    std::istringstream iss(request);
    std::string token;

    while (iss >> token) {
        auto it = action_string_to_code.find(token);
        if (it != action_string_to_code.end()) {
            serialized.push_back(it->second);
        }
    }

    serialized.push_back(NOP);  // Add NOP at the end

    return serialized;
}

std::string Serializer::deserialize(const std::vector<uint8_t>& request) {
    std::string result;
    for (const auto& action: request) {
        auto it = action_code_to_string.find(action);
        if (it != action_code_to_string.end()) {
            result += it->second;
            result += SPACE;
        }
    }

    result.pop_back();  // Remove the last space

    return result;
}
