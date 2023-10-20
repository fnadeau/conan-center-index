cmake_minimum_required(VERSION 3.15)
project(test_package CXX)

set(CMAKE_VERBOSE_MAKEFILE ON)

find_package(ads CONFIG REQUIRED)

if(${ADS_VERSION} VERSION_LESS 4.0.3)
    set(LIB ads::qtadvanceddocking)
else()
    set(LIB ads::qt5advanceddocking)
endif()

add_executable(${PROJECT_NAME} example.cpp)
target_link_libraries(${PROJECT_NAME} PRIVATE ${LIB})
