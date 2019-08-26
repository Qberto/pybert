__author__ = 'Alberto Nieto'
__version__ = "0.0.1"


""" Week 1; Exercise 3: Sequence to find the longest substring in alphabetical order in an input substring """
# Set an alphabet to check against
alphabet = 'abcdefghijklmnopqrstuvwxyz'

# Set data for longest substring to be empty
longest_substring = ''
current_record = len(longest_substring)

print("Checking each character...")
# Check each character of s and apply an index to easily reference against the string order
for ix, char in enumerate(s):
    # Var to contain the current sequence being tested
    tested_substring = char
    print("\n>>>> Checking index {0}, character {1}".format(str(ix), char))
    # Get the alphabet index of the character
    char_ix = alphabet.index(char)
    print("Alphabet position: {0}".format(str(char_ix)))
    print("Checking following characters...")

    # Set a loop that checks each following character, determining if the loop can continue by
    # checking if the index stays the same or keeps incrementing
    incrementing_flag = True
    test_index = ix + 1
    test_alphabet_ix = char_ix
    print("Starting test loop.")
    while incrementing_flag and test_index < len(s):
        # Get the next character
        test_char = s[test_index]
        print("\nNext character: {0}, test_index: {1}, alphabet index: {2}".format(test_char, str(test_index),
                                                                                   str(alphabet.index(test_char))))
        # Check if the alphabet index is equal or greater
        if alphabet.index(test_char) >= test_alphabet_ix:
            print("Next character was in sequence... adding to the current test.")
            # Add the character to the current longest substring
            tested_substring += test_char
            # Increment the test index to continue to the next test character
            test_index += 1
            # Change the test alphabet index value since the next letter will check against it (rather than the first letter)
            test_alphabet_ix = alphabet.index(test_char)

        else:
            print("Next character was not in sequence... breaking test loop.")
            # Record the length of the longest sequence
            break

    # Our test of the sequence concluded - let's see if it's longer than the current record
    if len(tested_substring) > len(longest_substring):
        print("Current sequence '{0}' is longer than the previous record '{1}'!".format(str(tested_substring),
                                                                                        str(longest_substring)))
        longest_substring = tested_substring
    else:
        print("Current sequence '{0}' is NOT longer than the previous record '{1}'!".format(str(tested_substring),
                                                                                            str(longest_substring)))
        print("Continuing search...")

print("\n\n>>>> Search complete. <<<<")
print("Longest substring in alphabetical order is: {0}".format(longest_substring))
